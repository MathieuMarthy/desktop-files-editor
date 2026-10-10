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
