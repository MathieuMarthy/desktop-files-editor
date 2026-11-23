import pytest
from gi.repository import GLib

from src.models.desktop_model import DesktopModel
from src.models.save_model import save_model
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
    return DesktopModel(desktop_file_path=str(path), **kwargs)


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


def test_save_hidden_writes_no_display(user_dir, make_desktop_file):
    path = make_desktop_file(user_dir)

    save_model(model_for(path, app_name="Firefox", app_icon="firefox", is_hidden=True))

    assert read(path).get_boolean(KEYFILE_GROUP, "NoDisplay") is True
