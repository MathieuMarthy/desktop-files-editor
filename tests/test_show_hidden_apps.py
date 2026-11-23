from types import SimpleNamespace

import pytest
from gi.repository import Gio

from src.models.desktop_model import DesktopModel
from tests.conftest import HAS_GRESOURCE, SCHEMA_ID

pytestmark = pytest.mark.skipif(not HAS_GRESOURCE, reason="needs a meson build for the UI")

if HAS_GRESOURCE:
    from src.main import DesktopFilesEditorApplication
    from src.pages.sidebar import Sidebar


def test_hidden_apps_are_not_shown_by_default(settings):
    assert settings.get_boolean("show-hidden-apps") is False


def test_app_action_is_a_toggle_with_shortcut(settings):
    app = DesktopFilesEditorApplication()
    action = app.lookup_action("show-hidden-apps")

    assert action.get_state().get_boolean() is False
    assert app.get_accels_for_action("app.show-hidden-apps") == ["<Control>h"]

    action.activate(None)

    assert action.get_state().get_boolean() is True
    assert settings.get_boolean("show-hidden-apps") is True


def test_other_settings_instances_are_notified(settings):
    """The sidebar has its own Gio.Settings: it must see the change made by the app action."""
    changes = []
    settings.connect("changed::show-hidden-apps", lambda s, key: changes.append(s.get_boolean(key)))

    Gio.Settings(schema_id=SCHEMA_ID).set_boolean("show-hidden-apps", True)

    assert changes == [True]


def filter_row(settings, model: DesktopModel, search: str = "") -> bool:
    """Run Sidebar._filter on one row, without building the widget."""
    store = Gio.ListStore(item_type=DesktopModel)
    store.append(model)
    sidebar = SimpleNamespace(
        store=store,
        settings=settings,
        search_entry=SimpleNamespace(get_text=lambda: search),
    )
    row = SimpleNamespace(get_index=lambda: 0, get_title=lambda: model.app_name)
    return Sidebar._filter(sidebar, row)


def test_filter_shows_visible_apps(settings):
    assert filter_row(settings, DesktopModel(app_name="Firefox")) is True


def test_filter_hides_hidden_apps_by_default(settings):
    assert filter_row(settings, DesktopModel(app_name="Firefox", is_hidden=True)) is False


def test_filter_shows_hidden_apps_when_enabled(settings):
    settings.set_boolean("show-hidden-apps", True)

    assert filter_row(settings, DesktopModel(app_name="Firefox", is_hidden=True)) is True


@pytest.mark.parametrize(("search", "expected"), [("fire", True), ("gimp", False)])
def test_search_still_applies_to_hidden_apps(settings, search, expected):
    settings.set_boolean("show-hidden-apps", True)
    model = DesktopModel(app_name="Firefox", is_hidden=True)

    assert filter_row(settings, model, search) is expected
