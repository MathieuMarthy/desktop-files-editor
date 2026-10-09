# desktop-files-editor

An app to list and edit .desktop files on Linux

## Contributing

PRs are welcome !

Make sure your code passes all the tests and is well formatted
```sh
# Tests
meson test -C build

# Format
ruff check --fix src  # for python code
blueprint-compiler format -f src/**/*.blp  # for blueprint files
meson format -i -r  # for meson
```
