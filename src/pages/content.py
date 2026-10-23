from gettext import gettext as _

from gi.repository import Adw, GObject, Gtk

from ..models.desktop_model import DesktopModel
from ..utils.display_image import set_app_icon


@Gtk.Template(resource_path="/net/dzqdzq/DesktopFilesEditor/pages/content.ui")
class Content(Adw.NavigationPage):
    __gtype_name__ = "DesktopFilesEditorContent"

    selected_desktop = GObject.Property(type=DesktopModel)
    has_changes = GObject.Property(type=bool, default=False)

    app_icon: Gtk.Image = Gtk.Template.Child()

    stack: Gtk.Stack = Gtk.Template.Child()
    empty_page: Adw.StatusPage = Gtk.Template.Child()
    editor_page: Adw.PreferencesPage = Gtk.Template.Child()
    button_save: Gtk.Button = Gtk.Template.Child()

    # forms
    entry_app_name: Adw.EntryRow = Gtk.Template.Child()
    entry_app_icon: Adw.EntryRow = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("notify::selected-desktop", self._on_selected_desktop_changed)

    def _on_selected_desktop_changed(self, *_args):
        self.button_save.set_visible(self.selected_desktop is not None)

        if self.selected_desktop is None:
            self.stack.set_visible_child(self.empty_page)
        else:
            self.stack.set_visible_child(self.editor_page)
            set_app_icon(self.app_icon, self.selected_desktop.app_icon)

    @Gtk.Template.Callback()  # called by the copy path button
    def copy_path_to_clipboard(self, button: Gtk.Button):
        self.get_clipboard().set(self.selected_desktop.desktop_file_path)

        toast = Adw.Toast(title=_("Path copied to clipboard"))
        self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

    def _do_user_edit_model(self) -> bool:
        if self.selected_desktop is None:
            return False

        return (
            self.entry_app_name.get_text() != self.selected_desktop.app_name
            or self.entry_app_icon.get_text() != self.selected_desktop.app_icon
        )

    @Gtk.Template.Callback()  # trigger on all entryRow
    def on_field_change(self, *_args):
        self.has_changes = self._do_user_edit_model()

    @Gtk.Template.Callback()  # called by the save button
    def save_modifications(self, *_args):
        toast = Adw.Toast(title=_("Not Implemented yet"))
        self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
