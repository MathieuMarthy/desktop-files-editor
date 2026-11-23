from pathlib import Path

import pytest
from gi.repository import Gio

from src.models import scan_desktop_files as module
from src.models.desktop_model import DesktopModel
from src.models.scan_desktop_files import (
    load_desktop_model_from_file,
    scan_desktop_files,
    scan_directory,
)


def load(path: Path):
    return load_desktop_model_from_file(Gio.File.new_for_path(str(path)))


def load_valid(path: Path) -> DesktopModel:
    model = load(path)
    assert model is not None
    return model


# scan_directory


def test_scan_directory_keeps_only_desktop_files(tmp_path, make_desktop_file):
    make_desktop_file(tmp_path, "firefox.desktop")
    make_desktop_file(tmp_path, "gimp.desktop")
    (tmp_path / "notes.txt").write_text("hello")

    names = sorted(Path(str(file.get_path())).name for file in scan_directory(tmp_path))

    assert names == ["firefox.desktop", "gimp.desktop"]


def test_scan_directory_empty(tmp_path):
    assert scan_directory(tmp_path) == []


def test_scan_directory_missing(tmp_path):
    assert scan_directory(tmp_path / "nope") == []


def test_scan_directory_on_a_file(tmp_path, make_desktop_file):
    path = make_desktop_file(tmp_path)

    assert scan_directory(path) == []


def test_scan_directory_is_not_recursive(tmp_path, make_desktop_file):
    make_desktop_file(tmp_path / "sub", "nested.desktop")

    assert scan_directory(tmp_path) == []


@pytest.mark.parametrize("name", ["firefox.desktop.bak", "desktop", "firefox.Desktop"])
def test_scan_directory_ignores_other_extensions(tmp_path, make_desktop_file, name):
    make_desktop_file(tmp_path, name)

    assert scan_directory(tmp_path) == []


def test_scan_directory_returns_gio_files(tmp_path, make_desktop_file):
    path = make_desktop_file(tmp_path)

    (file,) = scan_directory(tmp_path)

    assert isinstance(file, Gio.File)
    assert file.get_path() == str(path)


# load_desktop_model_from_file


def test_load_complete_file(tmp_path, make_desktop_file):
    path = make_desktop_file(tmp_path)

    model = load_valid(path)

    assert model.app_name == "Firefox"
    assert model.app_icon == "firefox"
    assert model.desktop_file_path == str(path)


def test_load_without_icon(tmp_path, make_desktop_file):
    path = make_desktop_file(tmp_path, content="[Desktop Entry]\nName=App\n")

    assert load_valid(path).app_icon == ""


def test_load_without_name(tmp_path, make_desktop_file):
    path = make_desktop_file(tmp_path, content="[Desktop Entry]\nIcon=app\n")

    assert load(path) is None


def test_load_without_desktop_entry_group(tmp_path, make_desktop_file):
    path = make_desktop_file(tmp_path, content="[Other Group]\nName=App\n")

    assert load(path) is None


def test_load_invalid_content(tmp_path, make_desktop_file):
    path = make_desktop_file(tmp_path, content="not a desktop file")

    assert load(path) is None


def test_load_empty_file(tmp_path, make_desktop_file):
    path = make_desktop_file(tmp_path, content="")

    assert load(path) is None


def test_load_missing_file(tmp_path):
    assert load(tmp_path / "nope.desktop") is None


def test_load_directory(tmp_path):
    path = tmp_path / "folder.desktop"
    path.mkdir()

    assert load(path) is None


def test_load_broken_symlink(tmp_path):
    path = tmp_path / "broken.desktop"
    path.symlink_to(tmp_path / "target-that-does-not-exist.desktop")

    assert load(path) is None


LOCALIZED = "[Desktop Entry]\nName=Files\nName[fr]=Fichiers\n"


def test_load_uses_translated_name(tmp_path, make_desktop_file, monkeypatch):
    monkeypatch.setenv("LANGUAGE", "fr")
    path = make_desktop_file(tmp_path, content=LOCALIZED)

    assert load_valid(path).app_name == "Fichiers"


def test_load_falls_back_to_untranslated_name(tmp_path, make_desktop_file, monkeypatch):
    monkeypatch.setenv("LANGUAGE", "en")
    path = make_desktop_file(tmp_path, content=LOCALIZED)

    assert load_valid(path).app_name == "Files"


def test_load_with_comments_and_blank_lines(tmp_path, make_desktop_file):
    content = "# A comment\n\n[Desktop Entry]\n# Another one\nName=App\n\nIcon=app\n"
    path = make_desktop_file(tmp_path, content=content)

    model = load_valid(path)

    assert model.app_name == "App"
    assert model.app_icon == "app"


# scan_desktop_files


@pytest.fixture
def directories(tmp_path, monkeypatch):
    """Replace the real application folders with temporary ones."""
    user_dir = tmp_path / "user"
    system_dirs = [tmp_path / "system", tmp_path / "flatpak"]
    monkeypatch.setattr(module, "user_applications_dir", lambda: user_dir)
    monkeypatch.setattr(module, "system_applications_dirs", lambda: system_dirs)
    return user_dir, system_dirs


def test_scan_collects_all_directories(directories, make_desktop_file):
    user_dir, (system_dir, flatpak_dir) = directories
    make_desktop_file(user_dir, "a.desktop", "[Desktop Entry]\nName=A\n")
    make_desktop_file(system_dir, "b.desktop", "[Desktop Entry]\nName=B\n")
    make_desktop_file(flatpak_dir, "c.desktop", "[Desktop Entry]\nName=C\n")

    names = sorted(model.app_name for model in scan_desktop_files())

    assert names == ["A", "B", "C"]


def test_scan_skips_invalid_files(directories, make_desktop_file):
    user_dir, _ = directories
    make_desktop_file(user_dir, "valid.desktop")
    make_desktop_file(user_dir, "broken.desktop", "not a desktop file")

    names = [model.app_name for model in scan_desktop_files()]

    assert names == ["Firefox"]


def test_scan_with_missing_directories(directories, make_desktop_file):
    user_dir, _ = directories
    make_desktop_file(user_dir)

    assert len(scan_desktop_files()) == 1


def test_scan_without_any_file(directories):
    assert scan_desktop_files() == []


def test_scan_returns_user_files_first(directories, make_desktop_file):
    user_dir, (system_dir, _) = directories
    make_desktop_file(system_dir, "a.desktop", "[Desktop Entry]\nName=System\n")
    make_desktop_file(user_dir, "z.desktop", "[Desktop Entry]\nName=User\n")

    names = [model.app_name for model in scan_desktop_files()]

    assert names == ["User", "System"]


def test_scan_user_file_hides_system_file(directories, make_desktop_file):
    user_dir, (system_dir, _) = directories
    user_file = make_desktop_file(user_dir, "firefox.desktop", "[Desktop Entry]\nName=Custom\n")
    system_file = make_desktop_file(
        system_dir, "firefox.desktop", "[Desktop Entry]\nName=Firefox\n"
    )

    models = scan_desktop_files()

    assert [model.app_name for model in models] == ["Custom"]
    assert models[0].desktop_file_path == str(user_file)
    assert models[0].path_to_desktop_in_system == str(system_file)


def test_scan_user_file_links_the_first_system_file(directories, make_desktop_file):
    user_dir, (system_dir, flatpak_dir) = directories
    make_desktop_file(user_dir, "firefox.desktop", "[Desktop Entry]\nName=Custom\n")
    system_file = make_desktop_file(system_dir, "firefox.desktop", "[Desktop Entry]\nName=A\n")
    make_desktop_file(flatpak_dir, "firefox.desktop", "[Desktop Entry]\nName=B\n")

    models = scan_desktop_files()

    assert len(models) == 1
    assert models[0].path_to_desktop_in_system == str(system_file)


def test_scan_system_duplicates_keep_the_first_without_link(directories, make_desktop_file):
    _, (system_dir, flatpak_dir) = directories
    make_desktop_file(system_dir, "firefox.desktop", "[Desktop Entry]\nName=First\n")
    make_desktop_file(flatpak_dir, "firefox.desktop", "[Desktop Entry]\nName=Second\n")

    models = scan_desktop_files()

    assert [model.app_name for model in models] == ["First"]
    assert models[0].path_to_desktop_in_system == ""


def test_scan_file_without_duplicate_has_no_link(directories, make_desktop_file):
    user_dir, _ = directories
    make_desktop_file(user_dir)

    assert scan_desktop_files()[0].path_to_desktop_in_system == ""
