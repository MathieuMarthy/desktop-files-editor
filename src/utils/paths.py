import os
from pathlib import Path

IN_FLATPAK = Path("/.flatpak-info").exists()


def user_applications_dir() -> Path:
    data_home = os.environ.get("HOST_XDG_DATA_HOME") or os.environ.get(
        "XDG_DATA_HOME", str(Path.home() / ".local/share")
    )
    return Path(data_home) / "applications"


def system_applications_dirs() -> list[Path]:
    # In the sandbox, /usr is the runtime: the host one is mounted under /run/host
    prefix = Path("/run/host") if IN_FLATPAK else Path("/")
    return [
        prefix / "usr/share/applications",
        Path("/var/lib/flatpak/exports/share/applications"),
        user_applications_dir().parent / "flatpak/exports/share/applications",
    ]
