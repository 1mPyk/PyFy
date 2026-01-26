from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QGraphicsDropShadowEffect,
    QInputDialog,
    QMenu,
    QMessageBox,
)
import os
from config.constants import COVERS_DIR
from utils.logger import logger


class AnimatedButton(QPushButton):
    def __init__(self, text="", style_type="primary"):
        super().__init__(text)
        self.style_type = style_type
        self.setFocusPolicy(Qt.NoFocus)
        self.setup_style()
        self.setup_shadow()

    def setup_style(self):
        styles = {
            "primary": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4a9eff, stop:1 #0066cc);
                    border: none;
                    border-radius: 10px;
                    color: white;
                    font-weight: bold;
                    padding: 8px 14px;
                }
                QPushButton:hover { opacity: 0.95; }
            """,
            "secondary": """
                QPushButton {
                    background: rgba(255,255,255,0.06);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 10px;
                    color: #e8e8e8;
                    padding: 6px 12px;
                }
                QPushButton:hover { background: rgba(255,255,255,0.09); }
            """,
            "icon": """
                QPushButton {
                    background: rgba(255,255,255,0.04);
                    border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 8px;
                    color: #cfcfcf;
                    font-size: 15px;
                }
                QPushButton:hover { background: rgba(255,255,255,0.06); color: white; }
            """,
        }
        self.setStyleSheet(styles.get(self.style_type, styles["primary"]))

    def setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 110))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)


class SongItemWidget(QWidget):
    def _t(self, key: str) -> str:
        return self.ui._t(key)

    def __init__(self, title, fullpath, parent_ui):
        super().__init__()
        self.title = title
        self.fullpath = fullpath
        self.ui = parent_ui
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        # clickable label ~70%
        self.label = QLabel(self.title)
        self.label.setStyleSheet("color: white; font-size: 14px;")
        self.label.setMinimumHeight(36)
        # single click plays
        self.label.mousePressEvent = self._on_play_click
        layout.addWidget(self.label, 7)

        # like button (shows heart if liked)
        liked = self.fullpath in self.ui.liked_songs
        self.like_btn = AnimatedButton("💖" if liked else "❤️", "icon")
        self.like_btn.setFixedSize(36, 30)
        self.like_btn.setStyleSheet("padding: 2px;")
        self.like_btn.clicked.connect(self._toggle_like)
        layout.addWidget(self.like_btn, 1)

        # add to playlist button
        self.add_btn = AnimatedButton("＋", "icon")
        self.add_btn.setFixedSize(36, 30)
        self.add_btn.setStyleSheet("padding: 2px;")
        self.add_btn.clicked.connect(self._show_add_menu)
        layout.addWidget(self.add_btn, 1)

        # remove from current playlist
        self.remove_btn = AnimatedButton("−", "icon")
        self.remove_btn.setFixedSize(36, 30)
        self.remove_btn.clicked.connect(self._remove_from_current)
        layout.addWidget(self.remove_btn, 1)

    def _on_play_click(self, evt):
        # find index in UI current playlist
        try:
            idx = self.ui.current_playlist.index(self.fullpath)
        except ValueError:
            idx = -1
        if idx >= 0:
            self.ui.play_song(idx)

    def _toggle_like(self):
        if self.fullpath in self.ui.liked_songs:
            self.ui.liked_songs.remove(self.fullpath)
            self.like_btn.setText("❤️")
        else:
            self.ui.liked_songs.append(self.fullpath)
            self.like_btn.setText("💖")
        self.ui.save_liked()
        self.ui.refresh_current_view()

    def _show_add_menu(self):
        menu = QMenu(self)
        menu.addAction(self._t("menu_create_playlist"))
        menu.addSeparator()
        for name in self.ui.playlists.keys():
            menu.addAction(name)
        action = menu.exec_(self.add_btn.mapToGlobal(self.add_btn.rect().bottomLeft()))
        if not action:
            return
        txt = action.text()
        if txt == self._t("menu_create_playlist"):
            try:
                name, ok = QInputDialog.getText(
                    self,
                    self._t("dlg_new_playlist_title"),
                    self._t("dlg_new_playlist_prompt"),
                )
                if ok and name:
                    name = name.strip()
                    if not name:
                        QMessageBox.warning(
                            self, self._t("msg_error_title"), "Name cannot be empty"
                        )
                        return
                    if name in self.ui.playlists:
                        QMessageBox.warning(
                            self,
                            self._t("msg_error_title"),
                            f"Playlist '{name}' already exists",
                        )
                        return
                    # Ensure we have a valid song path to add
                    song = getattr(self, "fullpath", None)
                    if not song:
                        QMessageBox.warning(
                            self, self._t("msg_error_title"), "No song selected to add"
                        )
                        return
                    # Create playlist containing the selected song (atomic)
                    self.ui.playlists[name] = [song]
                    self.ui.save_playlists()
                    self.ui._refresh_playlists_sidebar()
            except Exception as e:
                logger.exception("Error creating playlist from add menu: %s", e)
                QMessageBox.critical(self, self._t("msg_error_title"), str(e))
        else:
            if self.fullpath not in self.ui.playlists[txt]:
                self.ui.playlists[txt].append(self.fullpath)
                self.ui.save_playlists()

    def _remove_from_current(self):
        pname = self.ui.current_playlist_name
        path = self.fullpath

        if pname == "All Songs":
            self._delete_song_completely(path)
            return

        if pname and pname in self.ui.playlists:
            if path in self.ui.playlists[pname]:
                self.ui.playlists[pname].remove(path)
                self.ui.save_playlists()
                self.ui.load_playlist_view(pname)

    def _delete_song_completely(self, path):
        ui = self.ui
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            QMessageBox.critical(ui, "Error", f"Failed to delete file:\n{e}")
            return
        name = os.path.splitext(os.path.basename(path))[0]
        cover = os.path.join(COVERS_DIR, f"{name}.webp")
        if os.path.exists(cover):
            try:
                os.remove(cover)
            except Exception:
                pass
        for plist in ui.playlists.values():
            if path in plist:
                plist.remove(path)
        ui.save_playlists()
        ui._scan_songs_dir()


appstyle = """
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
