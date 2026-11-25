import pytest
from gi.repository import Gio

from src.models.delete_model import delete_model
from src.models.scan_desktop_files import load_desktop_model_from_file
from src.utils import paths


@pytest.fixture
def user_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "IN_FLATPAK", False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    return tmp_path / "data/applications"


def load(path):
    model = load_desktop_model_from_file(Gio.File.new_for_path(str(path)))
    assert model is not None
    return model


def test_delete_user_only_file(user_dir, make_desktop_file):
    path = make_desktop_file(user_dir)
    content = path.read_bytes()

    backup, original = delete_model(load(path))

    assert not path.exists()
    assert backup == content
    assert original is None


def test_delete_user_copy_returns_the_system_app(user_dir, tmp_path, make_desktop_file):
    system_file = make_desktop_file(tmp_path / "system")
    user_file = make_desktop_file(user_dir, content="[Desktop Entry]\nName=Custom\n")
    model = load(user_file)
    model.path_to_desktop_in_system = str(system_file)

    _, original = delete_model(model)

    assert not user_file.exists()
    assert system_file.exists()
    assert original is not None
    assert original.app_name == "Firefox"
    assert original.desktop_file_path == str(system_file)


def test_delete_user_copy_whose_system_file_is_gone(user_dir, tmp_path, make_desktop_file):
    user_file = make_desktop_file(user_dir)
    model = load(user_file)
    model.path_to_desktop_in_system = str(tmp_path / "system/firefox.desktop")

    _, original = delete_model(model)

    assert not user_file.exists()
    assert original is None  # treated like a user only file: the row is removed


def test_delete_refuses_system_files(user_dir, tmp_path, make_desktop_file):
    system_file = make_desktop_file(tmp_path / "system")

    with pytest.raises(ValueError):
        delete_model(load(system_file))

    assert system_file.exists()
