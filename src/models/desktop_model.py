from gi.repository import GObject


class DesktopModel(GObject.Object):
    __gtype_name__ = "DesktopFilesEditorDesktopModel"

    desktop_file_path = GObject.Property(type=str, default="")

    app_name = GObject.Property(type=str, default="")
    app_icon = GObject.Property(type=str, default="")
    is_hidden = GObject.Property(type=bool, default=False)
