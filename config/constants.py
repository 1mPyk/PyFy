import os
import sys
def get_current_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:  # если обычный .py
        return os.path.dirname(os.path.abspath(__file__))

VERSION = "1.3.11"
VERSION_URL = "https://raw.githubusercontent.com/PykHubOfficial/Testmain/refs/heads/main/versionPyFy.txt"
LAV_FILTERS_URL = "https://github.com/Nevcairiel/LAVFilters/releases/"
LAV_FILTERS_DIRECT = ""
ICONS_PACK_ZIP = ("https://github.com/PykHubOfficial/Testmain/raw/refs/heads/main/icons_pack.zip")
CONFIG_DIR1 = os.path.join("local", "cfg")
SONGS_DIR1 = os.path.join("local", "data", "Songs")
SONGS_DIR = os.path.join(get_current_path(), SONGS_DIR1)
CONFIG_DIR = os.path.join(get_current_path(), CONFIG_DIR1)
ICON1 = os.path.dirname(get_current_path())
ICON = os.path.join(ICON1, "app.ico")
LAST_PLAYLIST_FILE = os.path.join(CONFIG_DIR, "last_playlist.json")
LIKED_FILE = os.path.join(CONFIG_DIR, "liked.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")
VOLUME_FILE = os.path.join(CONFIG_DIR, "volume.json")
PLAYLISTS_FILE = os.path.join(CONFIG_DIR, "playlists.json")
ICONS_DIR1 = os.path.join("local", "data", "imgs")
ICONS_DIR = os.path.join(get_current_path(), ICONS_DIR1)
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
downloading_path = os.path.join(os.path.dirname(get_current_path()), "download.png")
COVERS_DIR1 = os.path.join("local", "data", "Covers")
COVERS_DIR = os.path.join(get_current_path(), COVERS_DIR1)
downloadupdate_path = os.path.join(os.path.dirname(get_current_path()), "downloadupdate.png")