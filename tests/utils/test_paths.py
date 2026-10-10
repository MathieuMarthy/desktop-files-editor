from pathlib import Path

import pytest

from src.utils import paths

FLATPAK_SYSTEM_EXPORTS = Path("/var/lib/flatpak/exports/share/applications")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("HOST_XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)


# user_applications_dir


def test_user_dir_uses_host_xdg_data_home(monkeypatch):
    monkeypatch.setenv("HOST_XDG_DATA_HOME", "/host/data")

    assert paths.user_applications_dir() == Path("/host/data/applications")


def test_user_dir_prefers_host_over_xdg_data_home(monkeypatch):
    monkeypatch.setenv("HOST_XDG_DATA_HOME", "/host/data")
    monkeypatch.setenv("XDG_DATA_HOME", "/sandbox/data")

    assert paths.user_applications_dir() == Path("/host/data/applications")


def test_user_dir_uses_xdg_data_home(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")

    assert paths.user_applications_dir() == Path("/custom/data/applications")


def test_user_dir_ignores_empty_host_xdg_data_home(monkeypatch):
    monkeypatch.setenv("HOST_XDG_DATA_HOME", "")
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")

    assert paths.user_applications_dir() == Path("/custom/data/applications")


def test_user_dir_falls_back_to_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    assert paths.user_applications_dir() == tmp_path / ".local/share/applications"


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
