import logging
from pathlib import Path

from gi.repository import Gio, GLib

from ..utils.const import KEYFILE_GROUP, LOCALIZED_KEYS, STRING_KEYS
from ..utils.paths import system_applications_dirs, user_applications_dir
from .desktop_model import DesktopModel

logger = logging.getLogger(__name__)


def scan_desktop_files() -> list[DesktopModel]:
    """
    Scan the application folders, by priority order (user folder first).
    When several files share the same name, only the first one is kept, like the desktop does.
    If the kept file is the user's copy, it remembers the path of the system file it overrides.
    """
    user_dir = user_applications_dir()
    directories_to_scan = [user_dir, *system_applications_dirs()]

    desktop_files: list[Gio.File] = []
    for path in directories_to_scan:
        desktop_files.extend(scan_directory(path))

    kept: dict[str, DesktopModel] = {}
    for file in desktop_files:
        model = load_desktop_model_from_file(file)
        if model is None:
            continue

        first = kept.setdefault(model.desktop_filename, model)
        if (
            first is not model
            and not first.path_to_desktop_in_system
            and Path(first.desktop_file_path).is_relative_to(user_dir)
        ):
            first.path_to_desktop_in_system = model.desktop_file_path

    return list(kept.values())


def scan_directory(path: Path) -> list[Gio.File]:
    directory = Gio.File.new_for_path(str(path))

    try:
        enumerator = directory.enumerate_children(
            "standard::name", Gio.FileQueryInfoFlags.NONE, None
        )
    except GLib.Error as error:
        logger.debug("Cannot scan the path %s: %s", path, error.message)
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
        keys = key_file.get_keys(KEYFILE_GROUP)[0]

        if "Name" not in keys:
            raise GLib.Error("no Name key")

        values = {
            prop: _get_string(key_file, key) for key, prop in STRING_KEYS.items() if key in keys
        }
        is_hidden = "NoDisplay" in keys and key_file.get_boolean(KEYFILE_GROUP, "NoDisplay")
    except GLib.Error as error:
        logger.warning("Failed to open and read the file %s: %s", file_path, error.message)
        return None

    return DesktopModel(desktop_file_path=file_path, is_hidden=is_hidden, **values)


def _get_string(key_file: GLib.KeyFile, key: str) -> str:
    if key in LOCALIZED_KEYS:
        return key_file.get_locale_string(KEYFILE_GROUP, key, None)

    return key_file.get_string(KEYFILE_GROUP, key)
