KEYFILE_GROUP = "Desktop Entry"

# text keys of a .desktop file -> DesktopModel property holding their value
STRING_KEYS = {
    "Name": "app_name",
    "Comment": "comment",
    "Icon": "app_icon",
    "Exec": "exec_command",
}
# keys read and written in the user's language
LOCALIZED_KEYS = {"Name", "Comment"}
# keys that cannot be emptied once in the file: the launcher would stop working
REQUIRED_KEYS = {"Name", "Exec"}
