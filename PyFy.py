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
    app.setStyleSheet(
        """
        QWidget { font-family: 'Segoe UI', Arial, sans-serif; color: white; }
        QLabel { color: white; }

        QMenu {
            background-color: #252426;
            border: 1px solid #3a3a3b;
            border-radius: 8px;
            padding: 6px;
        }
        QMenu::item {
            padding: 6px 20px;
            color: white;
            border-radius: 6px;
        }
        QMenu::item:selected { background: #3a3a3b; }

        QDialog, QInputDialog, QMessageBox {
            background-color: #252426;
            border-radius: 12px;
            border: none;
        }

        QLineEdit {
            background-color: #1c1c1d;
            color: white;
            border: 1px solid #3a3a3b;
            border-radius: 6px;
            padding: 4px 8px;
        }
        QPushButton {
            background: #3a3a3b;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
        }
        QPushButton:hover { background: #4a9eff; }
    """
    )

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