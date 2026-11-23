import logging
from pathlib import Path

from gi.repository import GLib

from ..models.desktop_model import DesktopModel
from ..utils.const import KEYFILE_GROUP
from ..utils.paths import user_applications_dir

logger = logging.getLogger(__name__)


def save_model(desktop_model: DesktopModel) -> str:
    """
    Save the model to file.
    If the model comes from a system folder, a new .desktop is created in the user folder.

    returns:
        (str): path where the desktop model has been saved
    """
    key_file = GLib.KeyFile()
    key_file.load_from_file(
        desktop_model.desktop_file_path,
        GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS,
    )

    # write the name in the locale it was read from (None or "C" = untranslated value)
    locale = key_file.get_locale_for_key(KEYFILE_GROUP, "Name", None)
    logger.debug("locale of the key_file: %s", locale)
    if locale and locale != "C":
        key_file.set_locale_string(KEYFILE_GROUP, "Name", locale, desktop_model.app_name)
    else:
        key_file.set_string(KEYFILE_GROUP, "Name", desktop_model.app_name)

    # optional keys: only written if they have a value or were already in the file
    existing_keys = key_file.get_keys(KEYFILE_GROUP)[0]
    if desktop_model.app_icon or "Icon" in existing_keys:
        key_file.set_string(KEYFILE_GROUP, "Icon", desktop_model.app_icon)
    if desktop_model.is_hidden or "NoDisplay" in existing_keys:
        key_file.set_boolean(KEYFILE_GROUP, "NoDisplay", desktop_model.is_hidden)

    path = Path(desktop_model.desktop_file_path)
    if not desktop_model.file_in_users_files:
        # file in a system folder: save a copy in the user folder
        user_dir = user_applications_dir()
        user_dir.mkdir(parents=True, exist_ok=True)
        path = user_dir / path.name

    key_file.save_to_file(str(path))
    logger.info(".desktop file of %s saved at %s", desktop_model.app_name, path)
    return str(path)
