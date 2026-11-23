# main.py
#
# Copyright 2026 mathieu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import os
import sys
from gettext import gettext as _

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402

from .utils.paths import icon_search_dirs  # noqa: E402
from .window import DesktopFilesEditorWindow  # noqa: E402


class DesktopFilesEditorApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="net.dzqdzq.DesktopFilesEditor",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            resource_base_path="/net/dzqdzq/DesktopFilesEditor",
        )
        self.create_action("quit", lambda *_: self.quit(), ["<control>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)
        self.create_action("search", self.on_search_action, ["<control>f"])
        self.create_action("save", self.on_save_action, ["<control>s"])

    def do_startup(self):
        Adw.Application.do_startup(self)

        # Make the icons of the host and of the Flatpak apps visible from the sandbox
        display = Gdk.Display.get_default()
        if display is None:
            return
        theme = Gtk.IconTheme.get_for_display(display)
        for directory in icon_search_dirs():
            theme.add_search_path(str(directory))

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = DesktopFilesEditorWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name="Desktop-files-editor",
            application_icon="net.dzqdzq.DesktopFilesEditor",
            developer_name="mathieu",
            version="0.1.0",
            # Translators: Replace "translator-credits" with your name/username,
            # and optionally an email or URL.
            translator_credits=_("translator-credits"),
            developers=["Mathieu Marthy"],
            copyright="© 2026 Mathieu Marthy",
        )
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        pass

    def on_search_action(self, *_):
        search_bar: Gtk.SearchBar = self.props.active_window.sidebar.search_bar  # type: ignore

        is_search_mode_active = search_bar.get_search_mode()
        search_bar.set_search_mode(not is_search_mode_active)

    def on_save_action(self, *_):
        if self.props.active_window is not None:
            self.props.active_window.content.save_modifications()  # type: ignore

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""

    logging.basicConfig(
        level=logging.DEBUG if os.environ.get("DFE_DEBUG") else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    app = DesktopFilesEditorApplication()
    return app.run(sys.argv)
