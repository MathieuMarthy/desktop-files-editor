from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from ..models.desktop_model import DesktopModel
from ..models.scan_desktop_files import scan_desktop_files
from ..utils.display_image import set_app_icon


@Gtk.Template(resource_path="/net/dzqdzq/DesktopFilesEditor/pages/sidebar.ui")
class Sidebar(Adw.NavigationPage):
    __gtype_name__ = "DesktopFilesEditorSideBar"

    list_box: Gtk.ListBox = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()

    selected_desktop = GObject.Property(type=DesktopModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.store = Gio.ListStore(item_type=DesktopModel)
        self.list_box.bind_model(self.store, self._create_row)
        self.settings = Gio.Settings(schema_id="net.dzqdzq.DesktopFilesEditor")
        self.settings.connect(
            "changed::show-hidden-apps", lambda *_: self.list_box.invalidate_filter()
        )

        self.list_box.set_filter_func(self._filter)

        self.refresh_list()

    def refresh_list(self):
        self.store.remove_all()

        models = scan_desktop_files()
        models = sorted(models, key=lambda model: GLib.utf8_collate_key(model.app_name, -1))
        for model in models:
            self.store.append(model)

    def add_and_select(self, model: DesktopModel) -> None:
        position = self.store.insert_sorted(model, _compare_names)
        self.list_box.select_row(self.list_box.get_row_at_index(position))  # pyright: ignore[reportArgumentType]

    def remove(self, model: DesktopModel) -> None:
        found, position = self.store.find(model)
        if found:
            self.store.remove(position)

    def _create_row(self, model: DesktopModel) -> Gtk.Widget:
        row = Adw.ActionRow(
            title=model.app_name,
            subtitle=(_("Hidden") if model.is_hidden else ""),
            use_markup=False,
        )
        model.bind_property("app-name", row, "title", GObject.BindingFlags.SYNC_CREATE)

        icon = Gtk.Image(pixel_size=32)
        set_app_icon(icon, model.app_icon)
        model.connect("notify::app-icon", lambda m, _pspec: set_app_icon(icon, m.app_icon))

        row.add_prefix(icon)
        return row

    @Gtk.Template.Callback()
    def on_row_selected(self, _, row: Gtk.ListBoxRow | None):
        if row is None:
            self.selected_desktop = None
            return

        self.selected_desktop = self.store.get_item(row.get_index())

    @Gtk.Template.Callback()
    def on_search_changed(self, _):
        self.list_box.invalidate_filter()

    def _filter(self, row: Adw.ActionRow) -> bool:
        model = self.store.get_item(row.get_index())

        if model is None or (model.is_hidden and not self.settings.get_boolean("show-hidden-apps")):
            return False

        return self.search_entry.get_text().lower().strip() in row.get_title().lower()


def _compare_names(a: DesktopModel, b: DesktopModel, *_user_data) -> int:
    """Sort by name in the user's language: case and accents don't push names to the end."""
    return GLib.utf8_collate(a.app_name, b.app_name)
