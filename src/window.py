# window.py
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

from gi.repository import Adw, Gtk

from .models.desktop_model import DesktopModel
from .pages.content import Content  # noqa: F401
from .pages.sidebar import Sidebar  # noqa: F401


@Gtk.Template(resource_path="/net/dzqdzq/DesktopFilesEditor/window.ui")
class DesktopFilesEditorWindow(Adw.ApplicationWindow):
    __gtype_name__ = "DesktopFilesEditorWindow"

    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    sidebar: Sidebar = Gtk.Template.Child()
    content: Content = Gtk.Template.Child()

    def show_toast(self, toast: Adw.Toast) -> None:
        self.toast_overlay.add_toast(toast)

    @Gtk.Template.Callback()
    def on_app_created(self, _content, model: DesktopModel) -> None:
        self.sidebar.add_and_select(model)
