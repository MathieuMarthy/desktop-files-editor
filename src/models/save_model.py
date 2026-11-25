import logging
from pathlib import Path

from gi.repository import GLib

from ..models.desktop_model import DesktopModel
from ..utils.const import KEYFILE_GROUP, LOCALIZED_KEYS, REQUIRED_KEYS, STRING_KEYS
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

    if desktop_model.new_app:
        key_file.set_string(KEYFILE_GROUP, "Type", "Application")
    else:
        key_file.load_from_file(
            desktop_model.desktop_file_path,
            GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS,
        )

    existing_keys = key_file.get_keys(KEYFILE_GROUP)[0]
    for key, prop in STRING_KEYS.items():
        value = getattr(desktop_model, prop)

        if value:
            _set_string(key_file, key, value)
        elif key in REQUIRED_KEYS and (key in existing_keys or desktop_model.new_app):
            logging.warning(f"can't save: {key} cannot be empty")
            raise ValueError(f"{key} cannot be empty")
        else:
            # remove the key and its translations, so the field is still empty on reload
            for existing in existing_keys:
                if existing == key or existing.startswith(f"{key}["):
                    key_file.remove_key(KEYFILE_GROUP, existing)

    if desktop_model.is_hidden or "NoDisplay" in existing_keys:
        key_file.set_boolean(KEYFILE_GROUP, "NoDisplay", desktop_model.is_hidden)

    path = Path(desktop_model.desktop_file_path)
    if not desktop_model.file_in_users_files:
        # file in a system folder: save a copy in the user folder
        user_dir = user_applications_dir()
        user_dir.mkdir(parents=True, exist_ok=True)
        path = user_dir / path.name

    if desktop_model.new_app and path.exists():
        raise FileExistsError("File already exists")

    key_file.save_to_file(str(path))
    logger.info(".desktop file of %s saved at %s", desktop_model.app_name, path)
    return str(path)


def _set_string(key_file: GLib.KeyFile, key: str, value: str) -> None:
    """Write the value in the locale it was read from ("C" = untranslated value)"""
    locale = key_file.get_locale_for_key(KEYFILE_GROUP, key, None)

    if key in LOCALIZED_KEYS and locale and locale != "C":
        key_file.set_locale_string(KEYFILE_GROUP, key, locale, value)
    else:
        key_file.set_string(KEYFILE_GROUP, key, value)
