from pathlib import Path

from gi.repository import Gtk

from .paths import host_path

FALLBACK_ICON = "application-x-executable"


def set_app_icon(image: Gtk.Image, icon: str) -> None:
    """Show the Icon= value of a desktop file in an existing Gtk.Image."""
    # Icon= is either a theme icon name or an absolute path to an image
    if Path(icon).is_absolute():
        path = host_path(icon)
        if path.is_file():
            image.set_from_file(str(path))
            return
        icon = ""

    theme = Gtk.IconTheme.get_for_display(image.get_display())
    if not icon or not theme.has_icon(icon):
        icon = FALLBACK_ICON
    image.set_from_icon_name(icon)
