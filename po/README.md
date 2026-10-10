# Translations

Translations use [gettext](https://www.gnu.org/software/gettext/) and live in this folder:

- `POTFILES.in`: source files containing translatable strings
- `LINGUAS`: enabled languages, one code per line
- `<lang>.po`: one translation file per language
- `desktop-files-editor.pot`: generated template (not committed)

All commands below are run from the project root.

## Setup (once)

Install the [development requirements](../README.md#requirements), then:

```sh
meson setup build
```

## Mark strings in the code

```python
from gettext import gettext as _, ngettext

_("Save")
_("“{name}” saved").format(name=name)  # never use an f-string inside _()
ngettext("{n} file", "{n} files", n).format(n=n)
```

```blueprint
label: _("Save");
title: C_("context", "Quit");
```

Every file containing marked strings must be listed in `POTFILES.in`.

## Update translations after changing strings

```sh
meson compile -C build desktop-files-editor-update-po
```

This regenerates the template and merges it into every `.po` file.
New strings are added empty, changed ones are marked `fuzzy`.

## Add a new language

```sh
meson compile -C build desktop-files-editor-pot
msginit -i po/desktop-files-editor.pot -o po/<lang>.po -l <lang> --no-translator
```

Then add `<lang>` to `LINGUAS` (keep it sorted).

## Translate

Open `po/<lang>.po` in [Translation Editor](https://flathub.org/apps/org.gnome.Gtranslator)
or [Poedit](https://flathub.org/apps/net.poedit.Poedit), fill in the strings,
and remove the `fuzzy` flags once reviewed.

Check the file for errors:

```sh
msgfmt --check --statistics -o /dev/null po/<lang>.po
```

## Test

Rebuild and install the Flatpak, then run:

```sh
flatpak run --env=LANGUAGE=<lang> net.dzqdzq.DesktopFilesEditor
```
