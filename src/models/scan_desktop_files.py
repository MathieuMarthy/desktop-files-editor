from pathlib import Path

from gi.repository import Gio, GLib

from ..utils.paths import system_applications_dirs, user_applications_dir
from .desktop_model import DesktopModel

KEYFILE_GROUP = "Desktop Entry"


def scan_desktop_files() -> list[DesktopModel]:

    directories_to_scan = [user_applications_dir(), *system_applications_dirs()]

    desktop_files: list[Gio.File] = []
    for path in directories_to_scan:
        desktop_files.extend(scan_directory(path))

    desktop_models = [load_desktop_model_from_file(file) for file in desktop_files]
    desktop_models = [file for file in desktop_models if file is not None]
    return desktop_models


def scan_directory(path: Path) -> list[Gio.File]:
    directory = Gio.File.new_for_path(str(path))

    try:
        enumerator = directory.enumerate_children(
            "standard::name", Gio.FileQueryInfoFlags.NONE, None
        )
    except GLib.Error:
        return []

    return [
        enumerator.get_child(info) for info in enumerator if info.get_name().endswith(".desktop")
    ]


def load_desktop_model_from_file(file: Gio.File) -> DesktopModel | None:
    key_file = GLib.KeyFile()
    file_path = str(file.get_path())

    try:
        key_file.load_from_file(
            file_path,
            GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS,
        )
        app_name = key_file.get_locale_string(KEYFILE_GROUP, "Name", None)
    except GLib.Error:
        return None

    app_icon = (
        key_file.get_string(KEYFILE_GROUP, "Icon")
        if "Icon" in key_file.get_keys(KEYFILE_GROUP)[0]
        else ""
    )

    return DesktopModel(desktop_file_path=file_path, app_name=app_name, app_icon=app_icon)
