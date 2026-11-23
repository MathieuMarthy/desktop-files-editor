import pytest

from src.models.desktop_model import DesktopModel


def test_default_values():
    model = DesktopModel()

    assert model.desktop_file_path == ""
    assert model.app_name == ""
    assert model.app_icon == ""


def test_constructor_sets_properties():
    model = DesktopModel(
        desktop_file_path="/tmp/firefox.desktop",
        app_name="Firefox",
        app_icon="firefox",
    )

    assert model.desktop_file_path == "/tmp/firefox.desktop"
    assert model.app_name == "Firefox"
    assert model.app_icon == "firefox"


def test_changing_property_emits_notify():
    model = DesktopModel(app_name="Firefox")
    notifications = []
    model.connect("notify::app-name", lambda obj, pspec: notifications.append(obj.app_name))

    model.app_name = "Fox"

    assert notifications == ["Fox"]


def test_unknown_property_is_rejected():
    with pytest.raises(TypeError):
        DesktopModel(foo="x")


def test_desktop_filename_follows_the_path():
    model = DesktopModel(desktop_file_path="/usr/share/applications/firefox.desktop")
    assert model.desktop_filename == "firefox.desktop"

    model.desktop_file_path = "/home/me/.local/share/applications/gimp.desktop"
    assert model.desktop_filename == "gimp.desktop"


def test_path_to_desktop_in_system_defaults_to_empty():
    assert DesktopModel().path_to_desktop_in_system == ""


def test_update_from_copies_every_property():
    model = DesktopModel(desktop_file_path="/a.desktop", app_name="A")
    other = DesktopModel(
        desktop_file_path="/b.desktop",
        app_name="B",
        app_icon="b-icon",
        is_hidden=True,
        path_to_desktop_in_system="/sys/b.desktop",
    )

    model.update_from(other)

    assert model.desktop_file_path == "/b.desktop"
    assert model.app_name == "B"
    assert model.app_icon == "b-icon"
    assert model.is_hidden is True
    assert model.path_to_desktop_in_system == "/sys/b.desktop"
