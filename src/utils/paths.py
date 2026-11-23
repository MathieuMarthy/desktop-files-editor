import os
from pathlib import Path

IN_FLATPAK = Path("/.flatpak-info").exists()


def user_data_dir() -> Path:
    if IN_FLATPAK:
        # In the sandbox, XDG_DATA_HOME is the app's private folder (~/.var/app/<id>/data).
        # Flatpak only sets HOST_XDG_DATA_HOME when XDG_DATA_HOME is set on the host.
        data_home = os.environ.get("HOST_XDG_DATA_HOME")
    else:
        data_home = os.environ.get("XDG_DATA_HOME")
    return Path(data_home) if data_home else Path.home() / ".local/share"


def host_path(path: str | Path) -> Path:
    """Return where a host path is visible from the app (in the sandbox, /usr is the runtime)."""
    path = Path(path)
    if IN_FLATPAK and path.is_relative_to("/usr"):
        return Path("/run/host") / path.relative_to("/")
    return path


def user_applications_dir() -> Path:
    return user_data_dir() / "applications"


def system_applications_dirs() -> list[Path]:
    # Same priority order as the desktop (XDG_DATA_DIRS): the first one wins on duplicates.
    # The host XDG_DATA_DIRS is not visible from the sandbox, so the usual order is hardcoded.
    return [
        user_data_dir() / "flatpak/exports/share/applications",
        Path("/var/lib/flatpak/exports/share/applications"),
        host_path("/usr/local/share/applications"),
        host_path("/usr/share/applications"),
    ]


def icon_search_dirs() -> list[Path]:
    return [
        user_data_dir() / "icons",
        user_data_dir() / "flatpak/exports/share/icons",
        Path("/var/lib/flatpak/exports/share/icons"),
        host_path("/usr/share/icons"),
        host_path("/usr/share/pixmaps"),
    ]


def is_in_user_applications_dir(path: str | Path) -> bool:
    return Path(path).is_relative_to(user_applications_dir())
