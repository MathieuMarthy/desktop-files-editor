import logging
from pathlib import Path

from gi.repository import Gio

from .desktop_model import DesktopModel
from .scan_desktop_files import load_desktop_model_from_file

logger = logging.getLogger(__name__)


def delete_model(desktop_model: DesktopModel) -> tuple[bytes, DesktopModel | None]:
    """
    Delete the user's .desktop file of the model.

    returns:
        (bytes): content of the deleted file, to write it back on undo
        (DesktopModel | None): the system app the file was overriding, now visible again
    """
    if not desktop_model.file_in_users_files:
        # system files are read only: never delete them, even if the app runs as root
        raise ValueError(f"{desktop_model.desktop_file_path} is not in the user folder")

    path = Path(desktop_model.desktop_file_path)
    backup = path.read_bytes()
    path.unlink()
    logger.info(".desktop file of %s deleted: %s", desktop_model.app_name, path)

    original = None
    if desktop_model.path_to_desktop_in_system:
        original = load_desktop_model_from_file(
            Gio.File.new_for_path(desktop_model.path_to_desktop_in_system)
        )
    return backup, original
