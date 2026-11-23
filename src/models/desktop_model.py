from pathlib import Path

from gi.repository import GObject

from ..utils.paths import is_in_user_applications_dir


class DesktopModel(GObject.Object):
    __gtype_name__ = "DesktopFilesEditorDesktopModel"

    desktop_file_path = GObject.Property(type=str, default="")
    # path of the system file overridden by this user file, "" if none
    path_to_desktop_in_system = GObject.Property(type=str, default="")

    app_name = GObject.Property(type=str, default="")
    app_icon = GObject.Property(type=str, default="")
    is_hidden = GObject.Property(type=bool, default=False)

    @property
    def desktop_filename(self) -> str:
        return Path(self.desktop_file_path).name

    @property
    def file_in_users_files(self) -> bool:
        return is_in_user_applications_dir(self.desktop_file_path)

    def update_from(self, other: "DesktopModel") -> None:
        """Copy every property of `other` into this model."""
        with self.freeze_notify():
            for pspec in other.list_properties():
                self.set_property(pspec.name, other.get_property(pspec.name))
