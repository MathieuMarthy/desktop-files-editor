import os
import subprocess
import tempfile
from pathlib import Path

import gi
import pytest

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gio  # noqa: E402

ROOT = Path(__file__).parent.parent
SCHEMA_ID = "net.dzqdzq.DesktopFilesEditor"

# Gio.Settings aborts the process if the schema is not compiled: compile the repo one,
# and keep the values in memory so the tests never touch the user's dconf.
_schema_dir = tempfile.TemporaryDirectory()
subprocess.run(
    ["glib-compile-schemas", f"--targetdir={_schema_dir.name}", str(ROOT / "data")], check=True
)
os.environ["GSETTINGS_SCHEMA_DIR"] = _schema_dir.name
os.environ["GSETTINGS_BACKEND"] = "memory"

# shortcut: the UI templates come from a meson build (newest of build/ and _build/),
# tests needing them are skipped without one; compile the blueprints here if CI runs pytest.
_gresources = sorted(
    ROOT.glob("*build/src/desktop-files-editor.gresource"), key=lambda p: p.stat().st_mtime
)
HAS_GRESOURCE = bool(_gresources)
if HAS_GRESOURCE:
    Gio.Resource.load(str(_gresources[-1]))._register()


@pytest.fixture
def settings():
    """App settings, reset to the defaults (the memory backend is shared by the whole run)."""
    settings = Gio.Settings(schema_id=SCHEMA_ID)
    for key in settings.props.settings_schema.list_keys():
        settings.reset(key)
    return settings


DEFAULT_CONTENT = """\
[Desktop Entry]
Type=Application
Name=Firefox
Icon=firefox
Exec=firefox %u
"""


@pytest.fixture
def make_desktop_file():
    def _make(directory: Path, name: str = "firefox.desktop", content: str = DEFAULT_CONTENT):
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        path.write_text(content)
        return path

    return _make
