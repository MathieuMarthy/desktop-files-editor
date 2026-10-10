from pathlib import Path

import pytest

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
