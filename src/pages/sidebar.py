from pathlib import Path

from gi.repository import Adw, Gio, Gtk

from ..models.desktop_model import DesktopModel
from ..models.scan_desktop_files import scan_desktop_files
from ..utils.paths import host_path

FALLBACK_ICON = "application-x-executable"


@Gtk.Template(resource_path="/net/dzqdzq/DesktopFilesEditor/pages/sidebar.ui")
class Sidebar(Adw.NavigationPage):
    __gtype_name__ = "DesktopFilesEditorSideBar"

    list_box: Gtk.ListBox = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.store = Gio.ListStore(item_type=DesktopModel)
        self.list_box.bind_model(self.store, self._create_row)

        self.refresh_list()

    def refresh_list(self):
        self.store.remove_all()

        for model in scan_desktop_files():
            if not model.is_hidden:
                self.store.append(model)

    def _create_row(self, model: DesktopModel) -> Gtk.Widget:
        row = Adw.ActionRow(
            title=model.app_name, subtitle=model.desktop_file_path, use_markup=False
        )
        row.add_prefix(self._create_icon(model.app_icon))
        return row

    def _create_icon(self, icon: str) -> Gtk.Image:
        # Icon= is either a theme icon name or an absolute path to an image
        if Path(icon).is_absolute():
            path = host_path(icon)
            if path.is_file():
                return Gtk.Image(file=str(path), pixel_size=32)
            icon = ""

        theme = Gtk.IconTheme.get_for_display(self.get_display())
        if not icon or not theme.has_icon(icon):
            icon = FALLBACK_ICON
        return Gtk.Image(icon_name=icon, pixel_size=32)

    @Gtk.Template.Callback()
    def on_row_selected(self, list_box: Gtk.ListBox, row: Gtk.ListBoxRow | None):
        if row is None:
            return

        model = self.store.get_item(row.get_index())
        if model is None:
            return

        print(f"{model.app_name=}{model.app_icon=}")
