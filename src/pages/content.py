import logging
import re
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, GLib, GObject, Gtk

from ..models.delete_model import delete_model
from ..models.desktop_model import DesktopModel
from ..models.save_model import save_model
from ..utils.display_image import set_app_icon
from ..utils.paths import unique_path, user_applications_dir

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/net/dzqdzq/DesktopFilesEditor/pages/content.ui")
class Content(Adw.NavigationPage):
    __gtype_name__ = "DesktopFilesEditorContent"
    __gsignals__ = {
        "app-created": (GObject.SignalFlags.RUN_FIRST, None, (DesktopModel,)),
        "app-deleted": (GObject.SignalFlags.RUN_FIRST, None, (DesktopModel,)),
    }

    selected_desktop = GObject.Property(type=DesktopModel)
    has_changes = GObject.Property(type=bool, default=False)

    app_icon: Gtk.Image = Gtk.Template.Child()

    stack: Gtk.Stack = Gtk.Template.Child()
    empty_page: Adw.StatusPage = Gtk.Template.Child()
    editor_page: Adw.PreferencesPage = Gtk.Template.Child()
    button_save: Gtk.Button = Gtk.Template.Child()
    button_delete: Adw.ButtonRow = Gtk.Template.Child()

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
        self._update_delete_button()

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
            new_app=self.selected_desktop.new_app,
        )

        # save the file
        try:
            new_desktop_path = save_model(desktop_model_to_save)
        except FileExistsError:
            toast = Adw.Toast(title=_("An application with this file name already exists"))
            self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
            return
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
        self._update_delete_button()  # a saved system file is now a user copy

        toast = Adw.Toast(title=_("Modifications saved"))
        self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

        if self.selected_desktop.new_app:
            self.selected_desktop.new_app = False
            self.emit("app-created", self.selected_desktop)

    @Gtk.Template.Callback()  # called by the name entry
    def on_name_change(self, _):
        if self.selected_desktop is None:
            return

        if self.selected_desktop.new_app:
            ascii_name = GLib.str_to_ascii(self.entry_app_name.get_text(), None).lower()
            slug = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")

            if slug == "":
                slug = "application"

            self.selected_desktop.desktop_file_path = str(
                unique_path(user_applications_dir() / f"{slug}.desktop")
            )
        self.on_field_change()

    def _update_delete_button(self):
        model = self.selected_desktop
        self.button_delete.set_visible(
            model is not None and model.file_in_users_files and not model.new_app
        )
        if model is not None and model.path_to_desktop_in_system:
            self.button_delete.set_title(_("Restore Original"))
        else:
            self.button_delete.set_title(_("Delete Application"))

    @Gtk.Template.Callback()  # called by the delete button
    def on_delete(self, _row):
        model = self.selected_desktop
        if model is None:
            return

        before = DesktopModel()
        before.update_from(model)
        try:
            backup, original = delete_model(model)
        except Exception:
            logger.exception("failed to delete %s", model.desktop_file_path)
            toast = Adw.Toast(title=_("Fail to delete the application"))
            self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
            return

        if original is not None:
            # the system app is visible again: the row stays, with the system values
            model.update_from(original)
            self._update_delete_button()
            title = _("Original restored")
        else:
            self.emit("app-deleted", model)
            title = _("Application deleted")

        toast = Adw.Toast(title=title, button_label=_("Undo"))
        toast.connect(
            "button-clicked", lambda _t: self._undo_delete(model, before, backup, original is None)
        )
        self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

    def _undo_delete(self, model: DesktopModel, before: DesktopModel, backup: bytes, removed: bool):
        try:
            Path(before.desktop_file_path).write_bytes(backup)
        except OSError:
            logger.exception("failed to restore %s", before.desktop_file_path)
            toast = Adw.Toast(title=_("Fail to restore the application"))
            self.get_root().show_toast(toast)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
            return

        model.update_from(before)
        self._update_delete_button()
        if removed:
            self.emit("app-created", model)  # re-inserts and selects it in the sidebar
