import os
from pathlib import Path

IN_FLATPAK = Path("/.flatpak-info").exists()


def user_data_dir() -> Path:
    data_home = os.environ.get("HOST_XDG_DATA_HOME") or os.environ.get(
        "XDG_DATA_HOME", str(Path.home() / ".local/share")
    )
    return Path(data_home)


def host_path(path: str | Path) -> Path:
    """Return where a host path is visible from the app (in the sandbox, /usr is the runtime)."""
    path = Path(path)
    if IN_FLATPAK and path.is_relative_to("/usr"):
        return Path("/run/host") / path.relative_to("/")
    return path


def user_applications_dir() -> Path:
    return user_data_dir() / "applications"


def system_applications_dirs() -> list[Path]:
    return [
        host_path("/usr/share/applications"),
        Path("/var/lib/flatpak/exports/share/applications"),
        user_data_dir() / "flatpak/exports/share/applications",
    ]


def icon_search_dirs() -> list[Path]:
    return [
        user_data_dir() / "icons",
        user_data_dir() / "flatpak/exports/share/icons",
        Path("/var/lib/flatpak/exports/share/icons"),
        host_path("/usr/share/icons"),
        host_path("/usr/share/pixmaps"),
    ]
