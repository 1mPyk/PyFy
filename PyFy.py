import sys
import os
import time
import shutil
from PyQt5.QtWidgets import QApplication
from languages import I18N
from config.constants import (
    SONGS_DIR,
    CONFIG_DIR,
    ICONS_DIR,
    downloading_path,
    downloadupdate_path,
)
from utils.files import ensure_dir
from ui.main_window import MusicPlayerUI
from ui.widgets import appstyle

ensure_dir(ICONS_DIR)
ensure_dir(CONFIG_DIR)
ensure_dir(SONGS_DIR)
if os.path.exists(downloading_path):
    shutil.move(downloading_path, ICONS_DIR)
if os.path.exists(downloadupdate_path):
    shutil.move(downloadupdate_path, ICONS_DIR)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(appstyle)

    w = MusicPlayerUI()
    w.show()

    if hasattr(w, "rpc"):
        w.rpc_running = False
        time.sleep(0.2)
        try:
            w.rpc.clear()
        except Exception:
            pass

    sys.exit(app.exec_())
