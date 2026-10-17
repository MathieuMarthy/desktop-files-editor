from gi.repository import GObject


class DesktopModel(GObject.Object):
    desktop_file_path = GObject.Property(type=str, default="")

    app_name = GObject.Property(type=str, default="")
    app_icon = GObject.Property(type=str, default="")
    is_hidden = GObject.Property(type=bool, default=False)
