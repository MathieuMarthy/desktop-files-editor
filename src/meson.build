pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'desktop_files_editor'
gnome = import('gnome')

blueprints = custom_target(
    'blueprints',
    input: files(
        'pages/content.blp',
        'pages/sidebar.blp',
        'shortcuts-dialog.blp',
        'window.blp',
    ),
    output: '.',
    command: [
        find_program('blueprint-compiler'),
        'batch-compile',
        '@OUTPUT@',
        '@CURRENT_SOURCE_DIR@',
        '@INPUT@',
    ],
)

gnome.compile_resources(
    'desktop-files-editor',
    'desktop-files-editor.gresource.xml',
    gresource_bundle: true,
    install: true,
    install_dir: pkgdatadir,
    dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
    input: 'desktop-files-editor.in',
    output: 'desktop-files-editor',
    configuration: conf,
    install: true,
    install_dir: get_option('bindir'),
    install_mode: 'rwxr-xr-x'
)

desktop_files_editor_sources = [
    '__init__.py',
    'main.py',
    'models/__init__.py',
    'models/desktop_model.py',
    'models/scan_desktop_files.py',
    'pages/__init__.py',
    'pages/content.py',
    'pages/sidebar.py',
    'utils/__init__.py',
    'utils/display_image.py',
    'utils/paths.py',
    'window.py',
]

install_data(
    desktop_files_editor_sources,
    install_dir: moduledir,
    preserve_path: true,
)
