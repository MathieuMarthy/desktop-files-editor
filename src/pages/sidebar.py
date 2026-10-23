from gi.repository import Adw, Gio, GObject, Gtk

from ..models.desktop_model import DesktopModel
from ..models.scan_desktop_files import scan_desktop_files
from ..utils.display_image import set_app_icon


@Gtk.Template(resource_path="/net/dzqdzq/DesktopFilesEditor/pages/sidebar.ui")
class Sidebar(Adw.NavigationPage):
    __gtype_name__ = "DesktopFilesEditorSideBar"

    list_box: Gtk.ListBox = Gtk.Template.Child()

    selected_desktop = GObject.Property(type=DesktopModel)

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
        row = Adw.ActionRow(title=model.app_name, use_markup=False)
        icon = Gtk.Image(pixel_size=32)
        set_app_icon(icon, model.app_icon)
        row.add_prefix(icon)
        return row

    @Gtk.Template.Callback()
    def on_row_selected(self, list_box: Gtk.ListBox, row: Gtk.ListBoxRow | None):
        if row is None:
            self.selected_desktop = None
            return

        self.selected_desktop = self.store.get_item(row.get_index())
