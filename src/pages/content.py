import logging
from gettext import gettext as _

from gi.repository import Adw, GObject, Gtk

from ..models.desktop_model import DesktopModel
from ..models.save_model import save_model
from ..utils.display_image import set_app_icon

logger = logging.getLogger(__name__)


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
    entry_comment: Adw.EntryRow = Gtk.Template.Child()
    entry_exec_command: Adw.EntryRow = Gtk.Template.Child()
    switch_is_hidden: Adw.SwitchRow = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # model watched for icon changes, and the id of its handler
        self._icon_watch: tuple[DesktopModel, int] | None = None
        self.connect("notify::selected-desktop", self._on_selected_desktop_changed)

    def _on_selected_desktop_changed(self, *_args):
        self.button_save.set_visible(self.selected_desktop is not None)

        if self._icon_watch is not None:
            model, handler_id = self._icon_watch
            model.disconnect(handler_id)
            self._icon_watch = None

        if self.selected_desktop is None:
            self.stack.set_visible_child(self.empty_page)
        else:
            self.stack.set_visible_child(self.editor_page)
            handler_id = self.selected_desktop.connect(
                "notify::app-icon", lambda m, _pspec: set_app_icon(self.app_icon, m.app_icon)
            )
            self._icon_watch = (self.selected_desktop, handler_id)
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
            or self.entry_comment.get_text() != self.selected_desktop.comment
            or self.entry_exec_command.get_text() != self.selected_desktop.exec_command
            or self.switch_is_hidden.get_active() != self.selected_desktop.is_hidden
        )

    @Gtk.Template.Callback()  # trigger on all entryRow
    def on_field_change(self, *_args):
        self.has_changes = self._do_user_edit_model()

    @Gtk.Template.Callback()  # called by the save button
    def save_modifications(self, *_args):
        if not self.has_changes:
            return

        desktop_model_to_save = DesktopModel(
            desktop_file_path=self.selected_desktop.desktop_file_path,
            app_name=self.entry_app_name.get_text(),
            app_icon=self.entry_app_icon.get_text(),
            comment=self.entry_comment.get_text(),
            exec_command=self.entry_exec_command.get_text(),
            is_hidden=self.switch_is_hidden.get_active(),
            path_to_desktop_in_system=self.selected_desktop.path_to_desktop_in_system,
        )

        # save the file
        try:
            new_desktop_path = save_model(desktop_model_to_save)
        except ValueError:
            toast = Adw.Toast(title=_("'Name' and 'Command' are required"))
            self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
            return
        except Exception:
            logger.exception("failed to save %s modifications", self.selected_desktop.app_name)
            toast = Adw.Toast(title=_("Fail to save modification"))
            self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
            return

        # update the model in the GUI
        old_path = self.selected_desktop.desktop_file_path
        if new_desktop_path != old_path:
            # a system file was copied in the user folder: remember the original
            desktop_model_to_save.desktop_file_path = new_desktop_path
            desktop_model_to_save.path_to_desktop_in_system = old_path

        self.selected_desktop.update_from(desktop_model_to_save)

        toast = Adw.Toast(title=_("Modifications saved"))
        self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
