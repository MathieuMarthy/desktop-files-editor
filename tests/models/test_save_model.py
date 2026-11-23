import pytest
from gi.repository import Gio, GLib

from src.models.desktop_model import DesktopModel
from src.models.save_model import save_model
from src.models.scan_desktop_files import load_desktop_model_from_file
from src.utils import paths
from src.utils.const import KEYFILE_GROUP


@pytest.fixture
def user_dir(tmp_path, monkeypatch):
    """Point the user data folder to a temp folder. The applications folder is not created."""
    monkeypatch.setattr(paths, "IN_FLATPAK", False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    return tmp_path / "data/applications"


def read(path) -> GLib.KeyFile:
    key_file = GLib.KeyFile()
    key_file.load_from_file(str(path), GLib.KeyFileFlags.KEEP_TRANSLATIONS)
    return key_file


def model_for(path, **kwargs) -> DesktopModel:
    """Model loaded from the file then edited, like the UI does."""
    model = load_desktop_model_from_file(Gio.File.new_for_path(str(path)))
    assert model is not None
    for name, value in kwargs.items():
        model.set_property(name, value)
    return model


def test_save_user_file_in_place(user_dir, make_desktop_file):
    path = make_desktop_file(user_dir)

    saved = save_model(model_for(path, app_name="Fox", app_icon="fox"))

    assert saved == str(path)
    key_file = read(path)
    assert key_file.get_string(KEYFILE_GROUP, "Name") == "Fox"
    assert key_file.get_string(KEYFILE_GROUP, "Icon") == "fox"


def test_save_system_file_creates_user_copy(user_dir, tmp_path, make_desktop_file):
    system_file = make_desktop_file(tmp_path / "system")

    saved = save_model(model_for(system_file, app_name="Fox", app_icon="firefox"))

    assert saved == str(user_dir / "firefox.desktop")
    assert read(saved).get_string(KEYFILE_GROUP, "Name") == "Fox"
    assert read(system_file).get_string(KEYFILE_GROUP, "Name") == "Firefox"


def test_save_keeps_other_keys(user_dir, make_desktop_file):
    path = make_desktop_file(user_dir)

    save_model(model_for(path, app_name="Fox", app_icon="firefox"))

    assert read(path).get_string(KEYFILE_GROUP, "Exec") == "firefox %u"


def test_save_untranslated_name_writes_no_locale_key(user_dir, make_desktop_file, monkeypatch):
    monkeypatch.setenv("LANGUAGE", "fr")
    path = make_desktop_file(user_dir)

    save_model(model_for(path, app_name="Fox", app_icon="firefox"))

    content = path.read_text()
    assert "Name=Fox" in content
    assert "Name[" not in content


def test_save_translated_name_in_its_locale(user_dir, make_desktop_file, monkeypatch):
    monkeypatch.setenv("LANGUAGE", "fr")
    path = make_desktop_file(
        user_dir, content="[Desktop Entry]\nName=Firefox\nName[fr]=Renard\nIcon=firefox\n"
    )

    save_model(model_for(path, app_name="Loup", app_icon="firefox"))

    key_file = read(path)
    assert key_file.get_locale_string(KEYFILE_GROUP, "Name", "fr") == "Loup"
    assert key_file.get_string(KEYFILE_GROUP, "Name") == "Firefox"


def test_save_does_not_add_empty_optional_keys(user_dir, make_desktop_file):
    path = make_desktop_file(user_dir, content="[Desktop Entry]\nName=Firefox\n")

    save_model(model_for(path, app_name="Fox"))

    content = path.read_text()
    assert "Icon" not in content
    assert "NoDisplay" not in content
    assert "Exec" not in content
    assert "Comment" not in content


def test_save_unchanged_model_round_trips(user_dir, make_desktop_file, monkeypatch):
    monkeypatch.setenv("LANGUAGE", "fr")
    content = (
        "[Desktop Entry]\nName=Firefox\nName[fr]=Renard\nComment=Browser\n"
        "Comment[fr]=Navigateur\nIcon=firefox\nExec=firefox %u\nNoDisplay=true\n"
    )
    path = make_desktop_file(user_dir, content=content)
    before = model_for(path)

    save_model(before)

    after = model_for(path)
    for pspec in before.list_properties():
        assert after.get_property(pspec.name) == before.get_property(pspec.name), pspec.name
    assert read(path).get_string(KEYFILE_GROUP, "Comment") == "Browser"


def test_save_hidden_writes_no_display(user_dir, make_desktop_file):
    path = make_desktop_file(user_dir)

    save_model(model_for(path, app_name="Firefox", app_icon="firefox", is_hidden=True))

    assert read(path).get_boolean(KEYFILE_GROUP, "NoDisplay") is True


def test_save_comment_in_its_own_locale(user_dir, make_desktop_file, monkeypatch):
    monkeypatch.setenv("LANGUAGE", "fr")
    content = "[Desktop Entry]\nName=Firefox\nComment=Browser\nComment[fr]=Navigateur\n"
    path = make_desktop_file(user_dir, content=content)

    save_model(model_for(path, app_name="Fox", comment="Butineur"))

    key_file = read(path)
    assert key_file.get_string(KEYFILE_GROUP, "Name") == "Fox"
    assert key_file.get_locale_string(KEYFILE_GROUP, "Comment", "fr") == "Butineur"
    assert key_file.get_string(KEYFILE_GROUP, "Comment") == "Browser"


def test_save_empty_comment_removes_it_and_its_translations(
    user_dir, make_desktop_file, monkeypatch
):
    monkeypatch.setenv("LANGUAGE", "fr")
    content = "[Desktop Entry]\nName=Firefox\nComment=Browser\nComment[fr]=Navigateur\n"
    path = make_desktop_file(user_dir, content=content)

    save_model(model_for(path, comment=""))

    assert "Comment" not in path.read_text()


def test_save_empty_exec_is_refused(user_dir, make_desktop_file):
    path = make_desktop_file(user_dir)

    with pytest.raises(ValueError):
        save_model(model_for(path, exec_command=""))

    assert read(path).get_string(KEYFILE_GROUP, "Exec") == "firefox %u"
