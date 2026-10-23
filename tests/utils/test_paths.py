from pathlib import Path

import pytest

from src.utils import paths

FLATPAK_SYSTEM_EXPORTS = Path("/var/lib/flatpak/exports/share/applications")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("HOST_XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(paths, "IN_FLATPAK", False)


@pytest.fixture
def home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


# user_applications_dir, outside Flatpak


def test_user_dir_uses_xdg_data_home(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")

    assert paths.user_applications_dir() == Path("/custom/data/applications")


def test_user_dir_ignores_host_xdg_data_home(monkeypatch, home):
    monkeypatch.setenv("HOST_XDG_DATA_HOME", "/host/data")

    assert paths.user_applications_dir() == home / ".local/share/applications"


def test_user_dir_falls_back_to_home(home):
    assert paths.user_applications_dir() == home / ".local/share/applications"


# user_applications_dir, inside Flatpak


def test_flatpak_user_dir_uses_host_xdg_data_home(monkeypatch):
    monkeypatch.setattr(paths, "IN_FLATPAK", True)
    monkeypatch.setenv("HOST_XDG_DATA_HOME", "/host/data")
    monkeypatch.setenv("XDG_DATA_HOME", "/sandbox/data")

    assert paths.user_applications_dir() == Path("/host/data/applications")


def test_flatpak_user_dir_ignores_sandbox_xdg_data_home(monkeypatch, home):
    # Real case: XDG_DATA_HOME points to ~/.var/app/<id>/data and HOST_XDG_DATA_HOME is unset
    monkeypatch.setattr(paths, "IN_FLATPAK", True)
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".var/app/net.dzqdzq.DesktopFilesEditor/data"))

    assert paths.user_applications_dir() == home / ".local/share/applications"


def test_flatpak_user_dir_ignores_empty_host_xdg_data_home(monkeypatch, home):
    monkeypatch.setattr(paths, "IN_FLATPAK", True)
    monkeypatch.setenv("HOST_XDG_DATA_HOME", "")

    assert paths.user_applications_dir() == home / ".local/share/applications"


# system_applications_dirs


def test_system_dirs_outside_flatpak(monkeypatch):
    monkeypatch.setattr(paths, "IN_FLATPAK", False)

    assert paths.system_applications_dirs()[0] == Path("/usr/share/applications")


def test_system_dirs_inside_flatpak(monkeypatch):
    monkeypatch.setattr(paths, "IN_FLATPAK", True)

    assert paths.system_applications_dirs()[0] == Path("/run/host/usr/share/applications")


@pytest.mark.parametrize("in_flatpak", [True, False])
def test_system_dirs_contain_flatpak_system_exports(monkeypatch, in_flatpak):
    monkeypatch.setattr(paths, "IN_FLATPAK", in_flatpak)

    assert FLATPAK_SYSTEM_EXPORTS in paths.system_applications_dirs()


def test_system_dirs_contain_flatpak_user_exports(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")

    expected = Path("/custom/data/flatpak/exports/share/applications")
    assert expected in paths.system_applications_dirs()


# host_path


def test_host_path_outside_flatpak(monkeypatch):
    monkeypatch.setattr(paths, "IN_FLATPAK", False)

    assert paths.host_path("/usr/share/pixmaps/app.png") == Path("/usr/share/pixmaps/app.png")


def test_host_path_inside_flatpak(monkeypatch):
    monkeypatch.setattr(paths, "IN_FLATPAK", True)

    expected = Path("/run/host/usr/share/pixmaps/app.png")
    assert paths.host_path("/usr/share/pixmaps/app.png") == expected


def test_host_path_inside_flatpak_keeps_other_paths(monkeypatch):
    monkeypatch.setattr(paths, "IN_FLATPAK", True)

    assert paths.host_path("/opt/app/icon.png") == Path("/opt/app/icon.png")


# icon_search_dirs


def test_icon_dirs_inside_flatpak(monkeypatch):
    monkeypatch.setattr(paths, "IN_FLATPAK", True)
    monkeypatch.setenv("HOST_XDG_DATA_HOME", "/custom/data")

    assert paths.icon_search_dirs() == [
        Path("/custom/data/icons"),
        Path("/custom/data/flatpak/exports/share/icons"),
        Path("/var/lib/flatpak/exports/share/icons"),
        Path("/run/host/usr/share/icons"),
        Path("/run/host/usr/share/pixmaps"),
    ]
