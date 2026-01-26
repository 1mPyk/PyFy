from PyQt5.QtCore import Qt, QTime, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QFrame,
    QFileDialog,
    QSlider,
    QListWidgetItem,
    QInputDialog,
    QMenu,
    QSizePolicy,
    QLineEdit,
    QMessageBox,
)
from pypresence import Presence
import subprocess
import os
import time
import threading
import json
from ui.settings import SettingsWindow
from languages import I18N
from utils.logger import logger
from config.constants import (
    ICON,
    PLAYLISTS_FILE,
    LAST_PLAYLIST_FILE,
    SETTINGS_FILE,
    LIKED_FILE,
    HISTORY_FILE,
    VOLUME_FILE,
    SONGS_DIR,
    COVERS_DIR,
    VERSION,
    get_current_path,
)
from ui.widgets import AnimatedButton, SongItemWidget
from ui.topbar import ModernTopBar
from utils.versions import get_latest_version, compare_versions


class MusicPlayerUI(QWidget):
    from core.player import (
        _toggle_play,
        _play_next,
        _update_rpc_time,
        _get_progress_bar,
        _toggle_repeat,
        _play_prev,
        play_song,
        _connect_and_play_path,
    )
    from core.downloader import (
        download_from_youtube,
        _on_download_finished,
        _on_download_error,
        _force_close_download_msg,
        show_download_history
    )

    def _t(self, key: str) -> str:
        lang = getattr(self, "language", "en")
        return I18N.get(lang, I18N["en"]).get(key, key)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyFy - Music Player")
        self.setWindowIcon(QIcon(ICON))
        logger.debug("ICON: %s", ICON)
        self.resize(1000, 640)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # container styling
        self.container = QWidget(self)
        self.container.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #15162b, stop:0.5 #101225, stop:1 #0b0b16);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.06);
            }
        """
        )
        self.container.setGeometry(0, 0, 1000, 640)

        # player
        self.player = QMediaPlayer()
        self.discord_client_id = (
            "1428734253239107624"  # вставь свой ID из Developer Portal
        )
        self.rpc = None
        try:
            self.rpc = Presence(self.discord_client_id)
            if getattr(self, "rpc_enabled", True):
                self.rpc.connect()
            logger.info("[Discord RPC] Connected")
        except Exception as e:
            logger.exception("[Discord RPC] Error: %s", e)

        self.rpc_thread = None
        self.rpc_running = False
        # таймер для авто-очистки статуса после длинной паузы
        self.pause_timer = QTimer(self)
        self.pause_timer.setSingleShot(True)
        self.pause_timer.timeout.connect(self._clear_presence_due_to_pause)
        self._pause_started_at = None

        # playback snapshot: used so repeat relates to the playlist snapshot where playback started
        self.playback_playlist = []
        self.playback_playlist_name = None

        # state
        self.current_playlist = []
        self.current_playlist_name = None
        self.current_index = -1
        self.repeat_mode = 0  # 0 off, 1 repeat playlist, 2 repeat single

        # data
        self.playlists = self._load_playlists()
        self.liked_songs = self._load_liked()
        self.listening_history = self._load_history()
        self.saved_volume = self._load_volume()
        # download history (recent downloads with status)
        self.download_history = []
        self.player.setVolume(self.saved_volume)
        self.load_settings()

        self._build_ui()
        self._connect_signals()
        self.apply_i18n()

        # Settings window
        self.settings_window = None

        # Таймер проверки обновлений (каждые 5 минут = 300000 мс)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start(300000)  # 5 минут

        # Первая проверка сразу при запуске
        QTimer.singleShot(2000, self.check_for_updates)  # через 2 секунды после запуска

        last_playlist = self._load_last_playlist()
        if last_playlist == "__liked__":
            self.load_playlist_view("__liked__")
            self.liked_btn.setStyleSheet(
                "background: #4a9eff; border-radius: 10px; color: white;"
            )
        elif last_playlist == "All Songs":
            self._scan_songs_dir()
            self.load_playlist_view("All Songs")
        elif last_playlist in self.playlists:
            self.load_playlist_view(last_playlist)
        else:
            self._scan_songs_dir()
            self.load_playlist_view("All Songs")

    def apply_i18n(self):
        t = self._t

        if hasattr(self, "topbar") and hasattr(self.topbar, "apply_i18n"):
            self.topbar.apply_i18n()

        # Можно через переводной ключ, если он есть
        try:
            self.setWindowTitle(t("app_title"))
        except Exception:
            self.setWindowTitle("PyFy - Music Player")

        mapping = [
            ("playlists_label", "playlists"),
            ("liked_btn", "liked_btn"),
            ("placeholder_label", "empty_placeholder"),
            ("add_songs_btn", "add_songs"),
            ("add_folder_btn", "add_folder"),
            ("create_playlist_btn", "create_playlist"),
            ("rescan_btn", "rescan"),
            ("restart_btn", "restart"),
            ("open_songs_dir_btn", "open_songs_dir"),
        ]
        for attr, key in mapping:
            if hasattr(self, attr):
                getattr(self, attr).setText(t(key))

    def download_from_youtube_bigpicture(self, text):
        self.topbar.url_input.setText(text)
        self.download_from_youtube()

    def _current_song_title(self):
        # пытаемся взять из текущего плейлиста; если не получилось — из снапшота воспроизведения
        path = None
        if (
            0
            <= getattr(self, "current_index", -1)
            < len(getattr(self, "current_playlist", []))
        ):
            path = self.current_playlist[self.current_index]
        elif (
            0
            <= getattr(self, "current_index", -1)
            < len(getattr(self, "playback_playlist", []))
        ):
            path = self.playback_playlist[self.current_index]

        if not path:
            return "Unknown"
        return os.path.splitext(os.path.basename(path))[0]

    def _on_state_changed(self, state):
        # Импорты уже есть: time, threading, os
        try:
            from PyQt5.QtMultimedia import QMediaPlayer
        except Exception:
            return
        if state == QMediaPlayer.PausedState:
            # показ "На паузе", старт 1800-сек. таймера очистки
            self._pause_started_at = time.time()
            self.rpc_running = False  # остановим поток обновления таймера
            self.pause_timer.start(1800_000)

            try:
                if self.rpc and getattr(self, "rpc_enabled", True):
                    song_title = self._current_song_title()
                    self.rpc.update(
                        details=f"🎵 {song_title}",
                        state="⏸ На паузе",
                        large_text="PyFy Music Player",
                    )
            except Exception as e:
                logger.exception("[Discord RPC Pause Update Error] %s", e)
        elif state == QMediaPlayer.PlayingState:
            # возобновление — отмена очистки и корректное время
            self.pause_timer.stop()
            self._pause_started_at = None

            try:
                if self.rpc and getattr(self, "rpc_enabled", True):
                    song_title = self._current_song_title()
                    # вычислим старт так, чтобы elapsed шёл от текущей позиции
                    start_time = int(time.time() - (self.player.position() // 1000))
                    self.rpc.update(
                        details=f"🎵 {song_title}",
                        state="Listening in PyFy",
                        start=start_time,
                        large_text="PyFy Music Player",
                    )

                    # перезапускаем поток “тикающего” времени
                    self.rpc_running = True
                    if getattr(self, "rpc_thread", None) and self.rpc_thread.is_alive():
                        self.rpc_running = False
                        time.sleep(0.2)
                    self.rpc_thread = threading.Thread(
                        target=self._update_rpc_time, args=(song_title,)
                    )
                    self.rpc_thread.daemon = True
                    self.rpc_thread.start()
            except Exception as e:
                logger.exception("[Discord RPC Resume Update Error] %s", e)
        else:
            # StoppedState или иное — сразу очищаем
            self.pause_timer.stop()
            self._pause_started_at = None
            self.rpc_running = False
            try:
                if self.rpc:
                    self.rpc.clear()
            except Exception:
                pass

    def _clear_presence_due_to_pause(self):
        try:
            if self.rpc:
                self.rpc.clear()
        except Exception:
            pass

    # ---------------------------
    # Storage helpers
    # ---------------------------
    def _load_json(self, path, default):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            return default
        return default

    def _save_json(self, path, data):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_playlists(self):
        data = self._load_json(PLAYLISTS_FILE, None)
        if not data:
            return {"All Songs": []}
        # Ensure keys exist
        if "All Songs" not in data:
            data["All Songs"] = []
        return data

    def _load_last_playlist(self):
        data = self._load_json(LAST_PLAYLIST_FILE, None)
        if data and isinstance(data, dict):
            return data.get("last_playlist", "All Songs")
        return "All Songs"

    def save_last_playlist(self, playlist_name):
        self._save_json(LAST_PLAYLIST_FILE, {"last_playlist": playlist_name})

    def load_settings(self):
        data = self._load_json(SETTINGS_FILE, {})
        self.show_covers_enabled = data.get("show_covers_enabled", True)
        self.language = data.get("language", "en")
        self.rpc_enabled = data.get("rpc_enabled", True)

    def save_settings(self):
        data = {
            "show_covers_enabled": self.show_covers_enabled,
            "language": getattr(self, "language", "en"),
            "rpc_enabled": getattr(self, "rpc_enabled", True),
        }
        self._save_json(SETTINGS_FILE, data)

    # ---------------------------
    # Center list click handlers
    # ---------------------------
    def _on_center_item_clicked(self, item):
        """Сохраняем индекс выбранного трека"""
        self.current_index = self.playlist_widget.row(item)

    def _on_center_item_double(self, item):
        """Двойной клик — сразу воспроизводим"""
        self.current_index = self.playlist_widget.row(item)
        self.play_song(self.current_index)

    def save_playlists(self):
        self._save_json(PLAYLISTS_FILE, self.playlists)

    def _load_liked(self):
        return self._load_json(LIKED_FILE, [])

    def save_liked(self):
        self._save_json(LIKED_FILE, self.liked_songs)

    def _load_history(self):
        return self._load_json(HISTORY_FILE, [])

    def save_history(self):
        self._save_json(HISTORY_FILE, self.listening_history)

    def _load_volume(self):
        return int(self._load_json(VOLUME_FILE, 50))

    def save_volume(self, v):
        self._save_json(VOLUME_FILE, int(v))

    # ---------------------------
    # UI build
    # ---------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # topbar
        self.topbar = ModernTopBar(self)
        main_layout.addWidget(self.topbar)

        # middle area with three columns
        mid = QHBoxLayout()
        mid.setContentsMargins(12, 12, 12, 12)
        mid.setSpacing(10)

        # left: playlists
        left_frame = QFrame()
        left_frame.setFixedWidth(240)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(8)
        self.playlists_label = QLabel("Playlists")
        left_layout.addWidget(self.playlists_label)
        self.playlists_list = QListWidget()
        self.playlists_list.setFixedWidth(220)
        self.playlists_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlists_list.customContextMenuRequested.connect(
            self._playlist_context_menu
        )
        left_layout.addWidget(self.playlists_list)
        self.playlists_list.itemClicked.connect(self.on_select_playlist)
        self.playlists_list.itemDoubleClicked.connect(self.on_select_playlist)

        self._refresh_playlists_sidebar()
        self.liked_btn = AnimatedButton("❤️ Liked", "secondary")
        # Use a dedicated handler to ensure sidebar selection is cleared when viewing liked songs
        self.liked_btn.clicked.connect(self.show_liked_view)
        left_layout.addWidget(self.liked_btn)
        mid.addWidget(left_frame)

        # center: playlist contents + placeholder
        center_frame = QFrame()
        center_layout = QVBoxLayout(center_frame)
        center_layout.setContentsMargins(6, 6, 6, 6)
        center_layout.setSpacing(8)
        self.placeholder_label = QLabel(self._t("empty_placeholder"))
        self.placeholder_label.setStyleSheet("color: rgba(200,200,200,0.6);")
        center_layout.addWidget(self.placeholder_label)
        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet(
            """
            QListWidget { background: transparent; color: white; }
            QListWidget::item:selected { background-color: rgba(74,158,255,0.18); }
        """
        )
        center_layout.addWidget(self.playlist_widget, 1)
        mid.addWidget(center_frame, 1)

        # right: controls
        right_frame = QFrame()
        right_frame.setFixedWidth(300)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(6, 0, 6, 6)
        right_layout.setSpacing(10)

        # отступ сверху
        right_layout.addSpacing(10)

        # квадрат/прямоугольник для обложки или информации
        self.cover_frame = QFrame()
        self.cover_frame.setFixedSize(285, 190)
        self.cover_frame.setStyleSheet(
            """
            QFrame {background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(74,158,255,0.15), stop:1 rgba(74,158,255,0.05));
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
            }
        """
        )
        cover_layout = QVBoxLayout(self.cover_frame)
        cover_layout.setAlignment(Qt.AlignCenter)
        # --- обложка ---
        self.cover_label = QLabel("🎵")
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cover_label.setStyleSheet(
            """
            QLabel {
                border-radius: 12px;
                background: transparent;
                font-size: 78px;
            }
        """
        )
        self.cover_label.setScaledContents(True)  # растягивает под размер
        cover_layout.addWidget(self.cover_label)

        # Принудительно делаем QLabel того же размера, что и frame:
        self.cover_label.resize(self.cover_frame.size())
        cover_layout.setContentsMargins(0, 0, 0, 0)
        cover_layout.setSpacing(0)
        self.cover_label.setMaximumSize(self.cover_frame.size())

        right_layout.addWidget(self.cover_frame)
        right_layout.addSpacing(10)

        # progress slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setStyleSheet(
            """
            QSlider::groove:horizontal { height:6px; background: rgba(255,255,255,0.12); border-radius:3px; }
            QSlider::handle:horizontal { background: #4a9eff; width:14px; height:14px; margin:-5px 0; border-radius:7px; }
        """
        )
        self.slider.setRange(0, 0)
        right_layout.addWidget(self.slider)

        # volume
        vol_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.saved_volume)
        vol_layout.addWidget(self.volume_slider)
        right_layout.addLayout(vol_layout)

        # time label под слайдером
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet(
            "color: rgba(255,255,255,0.7); font-size: 13px; border: none; background: transparent;"
        )
        self.time_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.time_label)
        right_layout.addSpacing(4)

        # playback buttons - без растягивания
        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        self.prev_btn = AnimatedButton("⏮", "icon")
        self.prev_btn.setFixedSize(60, 44)
        self.play_btn = AnimatedButton("▶", "primary")
        self.play_btn.setFixedSize(72, 44)
        self.next_btn = AnimatedButton("⏭", "icon")
        self.next_btn.setFixedSize(60, 44)
        self.repeat_btn = AnimatedButton("🔁", "icon")
        self.repeat_btn.setFixedSize(60, 44)
        self.prev_btn.setStyleSheet(
            """
                                    QPushButton {font-size: 16px; background-color: rgb(34,36,52)}
                                    QPushButton:hover {font-size: 18px;}
                                """
        )
        self.next_btn.setStyleSheet(
            """
                                    QPushButton {font-size: 16px; background-color: rgb(34,36,52)}
                                    QPushButton:hover {font-size: 18px;}
                                """
        )
        self.repeat_btn.setStyleSheet(
            """
                                    QPushButton {font-size: 16px; background-color: rgb(34,36,52)}
                                    QPushButton:hover {font-size: 18px;}
                                """
        )

        buttons.addWidget(self.prev_btn)
        buttons.addWidget(self.play_btn)
        buttons.addWidget(self.next_btn)
        buttons.addWidget(self.repeat_btn)
        buttons.setAlignment(Qt.AlignCenter)
        right_layout.addLayout(buttons)

        # add songs/folder, create playlist, rescan, restart
        self.add_songs_btn = AnimatedButton("+ Add Songs", "secondary")
        self.add_folder_btn = AnimatedButton("+ Add Folder", "secondary")
        self.create_playlist_btn = AnimatedButton("Create Playlist", "secondary")
        self.rescan_btn = AnimatedButton("Rescan Songs", "secondary")
        self.restart_btn = AnimatedButton("Restart", "secondary")
        self.open_songs_dir_btn = AnimatedButton("Open Songs Dir", "secondary")

        right_layout.addWidget(self.add_songs_btn)
        right_layout.addWidget(self.add_folder_btn)
        right_layout.addWidget(self.create_playlist_btn)
        right_layout.addWidget(self.rescan_btn)
        right_layout.addWidget(self.restart_btn)
        right_layout.addWidget(self.open_songs_dir_btn)

        mid.addWidget(right_frame)
        main_layout.addLayout(mid)

        # wire up smaller signals
        # playlist item widget clicks handled inside SongItemWidget
        self.playlist_widget.itemClicked.connect(self._on_center_item_clicked)
        self.playlist_widget.itemDoubleClicked.connect(self._on_center_item_double)
        # connect right-side buttons to methods later in _connect_signals

        # adjust initial placeholder visibility
        self._refresh_center_placeholder()

    # ---------------------------
    # Connect signals
    # ---------------------------
    def _connect_signals(self):
        # media signals
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.player.stateChanged.connect(self._on_state_changed)

        # persistent UI controls
        self.play_btn.clicked.connect(self._toggle_play)
        self.next_btn.clicked.connect(self._play_next)
        self.prev_btn.clicked.connect(self._play_prev)
        self.repeat_btn.clicked.connect(self._toggle_repeat)
        self.slider.sliderMoved.connect(self._set_position)
        self.volume_slider.valueChanged.connect(
            lambda v: (self.player.setVolume(v), self.save_volume(v))
        )
        # actions
        self.add_songs_btn.clicked.connect(self._add_songs_dialog)
        self.add_folder_btn.clicked.connect(self._add_folder_dialog)
        self.create_playlist_btn.clicked.connect(self._create_playlist_dialog)
        self.rescan_btn.clicked.connect(self._scan_songs_dir)
        self.restart_btn.clicked.connect(self._restart_app)
        self.open_songs_dir_btn.clicked.connect(self.open_songs_dir)

    def show_liked_view(self):
        """Show the virtual 'Liked' view and ensure no sidebar playlist remains selected."""
        try:
            # Load the liked virtual playlist
            self.load_playlist_view("__liked__")
        except Exception as e:
            logger.exception("Failed loading liked view: %s", e)
        # Highlight the liked button
        try:
            self.liked_btn.setStyleSheet(
                "background: #4a9eff; border-radius: 10px; color: white;"
            )
        except Exception:
            pass
        # Clear sidebar selection aggressively to avoid showing another playlist as selected
        try:
            sm = getattr(self.playlists_list, "selectionModel", None)
            if sm and sm():
                try:
                    self.playlists_list.selectionModel().clearSelection()
                except Exception:
                    pass
            try:
                self.playlists_list.clearSelection()
            except Exception:
                pass
            try:
                self.playlists_list.setCurrentRow(-1)
            except Exception:
                pass
            try:
                self.playlists_list.setCurrentItem(None)
            except Exception:
                pass
        except Exception:
            logger.exception("Error clearing sidebar selection for liked view")

    # ---------------------------
    # Playlist sidebar context menu
    # ---------------------------
    def _playlist_context_menu(self, pos):
        item = self.playlists_list.itemAt(pos)
        if item is None:
            return
        name = item.text()
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #252426;
                border: 1px solid #3a3a3b;
                border-radius: 4px;
                padding: 1px;
            }
            QMenu::item {
                padding: 3px 5px;
                color: white;
                background: transparent;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: #3a3a3b;
            }
        """
        )

        protected = ("All Songs", "__liked__")
        if name not in protected:
            rename_action = menu.addAction(self._t("menu_rename"))
            delete_action = menu.addAction(self._t("menu_delete"))

            action = menu.exec_(self.playlists_list.mapToGlobal(pos))
            if action == delete_action:
                self.playlists.pop(name, None)
                self.save_playlists()
                self._refresh_playlists_sidebar()
                # if current view was this playlist, clear center
                if self.current_playlist_name == name:
                    self.current_playlist = []
                    self.current_playlist_name = None
                    self._refresh_center_placeholder()
            elif action == rename_action:
                try:
                    newname, ok = QInputDialog.getText(
                        self, self._t("dlg_rename_title"), self._t("dlg_rename_prompt")
                    )
                    if ok and newname:
                        newname = newname.strip()
                        if not newname:
                            QMessageBox.warning(
                                self, self._t("msg_error_title"), "Name cannot be empty"
                            )
                            return
                        if newname in self.playlists:
                            QMessageBox.warning(
                                self,
                                self._t("msg_error_title"),
                                f"Playlist '{newname}' already exists",
                            )
                            return
                        # perform rename
                        self.playlists[newname] = self.playlists.pop(name)
                        self.save_playlists()
                        # Refresh sidebar and keep selection on renamed playlist
                        self._refresh_playlists_sidebar()
                        # select the renamed item in the list
                        matches = self.playlists_list.findItems(
                            newname, Qt.MatchExactly
                        )
                        if matches:
                            self.playlists_list.setCurrentItem(matches[0])
                        # if the renamed playlist was currently loaded, reload it under new name
                        if self.current_playlist_name == name:
                            self.load_playlist_view(newname)
                except Exception as e:
                    logger.exception(
                        "Error renaming playlist '%s' -> '%s': %s",
                        name,
                        newname if "newname" in locals() else None,
                        e,
                    )
                    QMessageBox.critical(self, self._t("msg_error_title"), str(e))

    # ---------------------------
    # Playlist / center helpers
    # ---------------------------
    def _refresh_playlists_sidebar(self):
        # Refresh the sidebar list and mark the current playlist visually
        self.playlists_list.clear()
        for name in self.playlists.keys():
            display_name = name
            # prefix the currently viewed playlist with a play indicator
            if (
                hasattr(self, "current_playlist_name")
                and self.current_playlist_name == name
            ):
                display_name = f"▶ {name}"
            item = QListWidgetItem(display_name)
            # store the raw playlist name in UserRole for later retrieval
            item.setData(Qt.UserRole, name)
            self.playlists_list.addItem(item)

        # ensure the selected item matches current view (if any)
        try:
            target = getattr(self, "current_playlist_name", None)
            if target is None and self.playlists_list.count() > 0:
                # default to 'All Songs' if present
                if "All Songs" in self.playlists:
                    target = "All Songs"
            if target:
                matches = self.playlists_list.findItems(f"▶ {target}", Qt.MatchExactly)
                if not matches:
                    matches = self.playlists_list.findItems(target, Qt.MatchExactly)
                if matches:
                    self.playlists_list.setCurrentItem(matches[0])
        except Exception:
            logger.exception("Error selecting playlist in sidebar")

        # If viewing Liked songs (a virtual view), clear any sidebar selection so no ▶ prefix remains
        try:
            if getattr(self, "current_playlist_name", None) == "__liked__":
                # explicitly clear current selection
                self.playlists_list.setCurrentItem(None)
        except Exception:
            pass

        # Slight visual tweak: selected item background color
        try:
            self.playlists_list.setStyleSheet(
                "QListWidget::item:selected{background: #4a9eff; color: white;}"
            )
        except Exception:
            pass

    def _refresh_center_placeholder(self):
        has_any = bool(any(self.playlists.values()) or self.liked_songs)
        if not has_any:
            self.placeholder_label.show()
            self.playlist_widget.hide()
        else:
            self.placeholder_label.hide()
            self.playlist_widget.show()

    def on_select_playlist(self, item):
        # item may contain a display prefix, use stored raw name when available
        playlist_name = item.data(Qt.UserRole) or item.text()
        # Load the playlist view (this may rebuild the sidebar and delete the original item)
        self.load_playlist_view(playlist_name)
        # After refresh, find the newly created QListWidgetItem and select it (avoid using deleted item)
        try:
            matches = self.playlists_list.findItems(
                f"▶ {playlist_name}", Qt.MatchExactly
            )
            if not matches:
                matches = self.playlists_list.findItems(playlist_name, Qt.MatchExactly)
            if matches:
                self.playlists_list.setCurrentItem(matches[0])
        except Exception:
            logger.exception("Error selecting playlist in on_select_playlist")

    def load_playlist_view(self, name):
        self.playlist_widget.clear()
        self.current_playlist_name = None
        tracks = []
        if name == "__liked__":
            tracks = list(self.liked_songs)
            self.current_playlist_name = "__liked__"
        else:
            tracks = self.playlists.get(name, [])
            self.current_playlist_name = name

        # Update liked button visual state: highlight when viewing liked songs, reset otherwise
        try:
            if hasattr(self, "liked_btn"):
                if self.current_playlist_name == "__liked__":
                    logger.debug("Setting liked button highlight (view=__liked__)")
                    self.liked_btn.setStyleSheet(
                        "background: #4a9eff; border-radius: 10px; color: white;"
                    )
                else:
                    logger.debug("Resetting liked button style (view!=__liked__)")
                    # Reset to AnimatedButton default style if possible
                    try:
                        self.liked_btn.setup_style()
                    except Exception:
                        self.liked_btn.setStyleSheet("")
        except Exception as e:
            logger.exception("Error updating liked button state: %s", e)

        if not tracks:
            self.current_playlist = []
            self.current_index = -1
            # Use i18n for empty playlist placeholder
            try:
                self.placeholder_label.setText(self._t("empty_placeholder"))
            except Exception:
                self.placeholder_label.setText(
                    "Playlist is empty — add songs or create a new one."
                )
            self.placeholder_label.show()
            self.playlist_widget.hide()
            return

        self.placeholder_label.hide()
        self.playlist_widget.show()
        for path in tracks:
            item = QListWidgetItem()
            w = SongItemWidget(os.path.splitext(os.path.basename(path))[0], path, self)
            item.setSizeHint(w.sizeHint())
            self.playlist_widget.addItem(item)
            self.playlist_widget.setItemWidget(item, w)

        self.current_playlist = list(tracks)
        self.current_index = -1

        # СОХРАНЯЕМ ВЫБРАННЫЙ ПЛЕЙЛИСТ
        self.save_last_playlist(name)
        # Update sidebar visuals to reflect currently loaded playlist
        try:
            self._refresh_playlists_sidebar()
        except Exception:
            logger.exception("Failed to refresh sidebar after loading playlist")

        # If we loaded the virtual "Liked" view, ensure no actual playlist remains selected
        try:
            if getattr(self, "current_playlist_name", None) == "__liked__":
                try:
                    self.playlists_list.clearSelection()
                except Exception:
                    # fallback to clearing current item
                    try:
                        self.playlists_list.setCurrentItem(None)
                    except Exception:
                        pass
        except Exception:
            logger.exception("Error clearing sidebar selection for liked view")

    # ---------------------------
    # Adding songs / folders / scan
    # ---------------------------
    def _add_songs_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, self._t("filedlg_select_songs"), "", self._t("filedlg_audio_filter")
        )
        if not files:
            return

        target = self.current_playlist_name or "All Songs"
        self.playlists.setdefault(target, [])
        changed = False
        for f in files:
            fp = os.path.normpath(f)
            if fp not in self.playlists[target]:
                self.playlists[target].append(fp)
                changed = True
            # добавляем также в "All Songs" как глобальный список
            if fp not in self.playlists.setdefault("All Songs", []):
                self.playlists["All Songs"].append(fp)

        if changed:
            self.save_playlists()
            self._refresh_playlists_sidebar()

        self.load_playlist_view(target)

    def _add_folder_dialog(self):
        d = QFileDialog.getExistingDirectory(self, self._t("filedlg_select_folder"))
        if not d:
            return
        self._add_songs_from_dir(d)
        self.load_playlist_view("All Songs")

    def _scan_songs_dir(self):
        # Добавляем все нужные форматы
        exts = (".mp3", ".wav", ".flac", ".m4a", ".aac", ".mp4", ".webm")
        found = []
        for base, dirs, files in os.walk(SONGS_DIR):
            for f in files:
                if f.lower().endswith(exts):
                    full = os.path.abspath(os.path.normpath(os.path.join(base, f)))
                    found.append(full)

        # убираем дубли
        found = list(dict.fromkeys(found))

        # пересохраняем All Songs заново
        self.playlists["All Songs"] = found

        self._refresh_playlists_sidebar()
        self.save_playlists()
        self.load_playlist_view("All Songs")

    def _add_songs_from_dir(self, root_dir):
        # такие же форматы
        exts = (".mp3", ".wav", ".flac", ".m4a", ".aac", ".mp4", ".webm")
        self.playlists.setdefault("All Songs", [])
        changed = False

        existing_names = {os.path.basename(p) for p in self.playlists["All Songs"]}

        for base, dirs, files in os.walk(root_dir):
            for f in files:
                if f.lower().endswith(exts):
                    full = os.path.abspath(os.path.normpath(os.path.join(base, f)))
                    if f not in existing_names:
                        self.playlists["All Songs"].append(full)
                        existing_names.add(f)
                        changed = True

        if changed:
            self.playlists["All Songs"] = list(
                dict.fromkeys(self.playlists["All Songs"])
            )
            self.save_playlists()

    def open_songs_dir(self):
        os.startfile(SONGS_DIR)

    # ---------------------------
    # Media callbacks
    # ---------------------------
    def _on_position_changed(self, pos):
        # pos in ms
        self.slider.blockSignals(True)
        self.slider.setValue(pos)
        self.slider.blockSignals(False)
        dur = self.player.duration()
        if dur > 0:
            cur = QTime(0, 0, 0).addMSecs(pos).toString("mm:ss")
            tot = QTime(0, 0, 0).addMSecs(dur).toString("mm:ss")
            self.time_label.setText(f"{cur} / {tot}")

    def _on_duration_changed(self, dur):
        if dur is None:
            dur = 0
        self.slider.setRange(0, max(0, dur))

    def _set_position(self, pos):
        self.player.setPosition(pos)

    def _on_media_status(self, status):
        # handle end of media
        from PyQt5.QtMultimedia import QMediaPlayer as MP

        if status == MP.EndOfMedia:
            # if repeat single
            pl = self.playback_playlist or self.current_playlist
            if self.repeat_mode == 2:
                # replay same track
                if 0 <= self.current_index < len(pl):
                    self.play_song(self.current_index)
                    return
            # else move to next or repeat playlist or pause
            if self.current_index + 1 < len(pl):
                self._play_next()
            elif self.repeat_mode == 1 and len(pl) > 0:
                self.play_song(0)
            else:
                self.player.pause()
                self.play_btn.setText("▶")

    # ---------------------------
    # small helpers / ui sync
    # ---------------------------
    def refresh_current_view(self):
        # ensure heart icons match liked_songs
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            widget = self.playlist_widget.itemWidget(item)
            if isinstance(widget, SongItemWidget):
                widget.like_btn.setText(
                    "💖" if widget.fullpath in self.liked_songs else "❤️"
                )

        # обновляем обложку текущего трека (без перезапуска)
        if self.current_index >= 0 and self.current_index < len(self.current_playlist):
            song_path = self.current_playlist[self.current_index]
            cover_name = os.path.splitext(os.path.basename(song_path))[0] + ".webp"
            cover_path = os.path.join(COVERS_DIR, cover_name)

            if self.show_covers_enabled and os.path.exists(cover_path):
                pix = QPixmap(cover_path).scaled(
                    285, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.cover_label.setPixmap(pix)
                self.cover_label.setText("")
            else:
                self.cover_label.setPixmap(QPixmap())
                self.cover_label.setText("🎵")

    # ---------------------------
    # Buttons actions: create playlist, add songs/folders, restart
    # ---------------------------
    def _create_playlist_dialog(self):
        try:
            name, ok = QInputDialog.getText(
                self,
                self._t("dlg_new_playlist_title"),
                self._t("dlg_new_playlist_prompt"),
            )
            if ok and name:
                if name in self.playlists:
                    QMessageBox.warning(
                        self,
                        self._t("msg_error_title"),
                        f"Playlist '{name}' already exists",
                    )
                    return
                self.playlists[name] = []
                self.save_playlists()
                self._refresh_playlists_sidebar()
        except Exception as e:
            logger.exception("Error in _create_playlist_dialog: %s", e)
            QMessageBox.critical(self, self._t("msg_error_title"), str(e))

    def _restart_app(self):
        update_path = os.path.join(os.path.join(get_current_path()), "PyFy.exe")
        if os.path.exists(update_path):
            subprocess.Popen([update_path])
        QApplication.exit(0)

    def show_settings(self):
        """Show settings window"""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
        self.settings_window.show()
        # Center on parent
        parent_geo = self.geometry()
        x = parent_geo.x() + (parent_geo.width() - self.settings_window.width()) // 2
        y = parent_geo.y() + (parent_geo.height() - self.settings_window.height()) // 2
        self.settings_window.move(x, y)

    def launch_big_picture_mode(self):
        from PyQt5.QtWidgets import (
            QMainWindow,
            QWidget,
            QFrame,
            QLabel,
            QListWidget,
            QListWidgetItem,
            QHBoxLayout,
            QVBoxLayout,
            QPushButton,
            QSlider,
            QStyledItemDelegate,
            QStyle,
        )
        from PyQt5.QtCore import Qt, QTimer, QSize, QRect, QRectF
        from PyQt5.QtGui import (
            QColor,
            QPainter,
            QRadialGradient,
            QPixmap,
            QFont,
            QPainterPath,
            QPen,
            QImage,
            QFontMetrics,
        )
        from random import randint, uniform
        import os

        # ====== Налаштування ======
        COVER_LEFT_MARGIN = 10
        COVER_SIZE = 520
        COVER_RADIUS = 30
        RIGHT_PANEL_WIDTH = 400
        COVER_IMAGE_SHIFT = 30  # зміщення фото вліво (0 = центр)

        # ---------- Label із контуром (для назви треку) ----------
        class OutlineLabel(QLabel):
            def __init__(
                self, text="", outline=2, color=QColor(255, 255, 255), parent=None
            ):
                super().__init__(text, parent)
                self.outline = outline
                self.color = color
                self.setStyleSheet("background: transparent;")
                self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing, True)

                text = self.text()
                font = self.font()
                fm = QFontMetrics(font)
                x = 2
                y = (self.height() + fm.ascent() - fm.descent()) // 2

                path = QPainterPath()
                path.addText(x, y, font, text)

                # чорний контур
                painter.setPen(
                    QPen(
                        QColor(0, 0, 0, 30),
                        self.outline,
                        cap=Qt.RoundCap,
                        join=Qt.RoundJoin,
                    )
                )
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

                # білий текст
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color)
                painter.drawPath(path)

        # ---------- Delegate для білих надписів з контуром (плейлісти + треки) ----------
        class OutlineItemDelegate(QStyledItemDelegate):
            def __init__(self, parent=None, outline=1.5, color=QColor(255, 255, 255)):
                super().__init__(parent)
                self.outline = outline
                self.color = color

            def paint(self, painter, option, index):
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing, True)

                rect = option.rect
                text = index.data()
                f = option.font
                painter.setFont(f)
                fm = QFontMetrics(f)

                x = rect.x() + 8
                y = rect.y() + (rect.height() + fm.ascent() - fm.descent()) // 2

                path = QPainterPath()
                path.addText(x, y, f, text)

                painter.setPen(
                    QPen(
                        QColor(0, 0, 0, 30),
                        self.outline,
                        cap=Qt.RoundCap,
                        join=Qt.RoundJoin,
                    )
                )
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

                # білий текст
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color)
                painter.drawPath(path)

                # фон для виділеного айтема
                if option.state & QStyle.State_Selected:
                    r = QRect(
                        rect.x() + 4, rect.y() + 2, rect.width() - 8, rect.height() - 4
                    )
                    painter.setBrush(QColor(255, 255, 255, 45))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(r, 8, 8)

                painter.restore()

        # ---------- Завантаження обкладинки з заокругленням і зміщенням фото вліво ----------
        def load_rounded_cover_with_shift(ui, w, h, radius, shift_x=0):
            try:
                if 0 <= ui.current_index < len(ui.current_playlist):
                    song_path = ui.current_playlist[ui.current_index]
                else:
                    return None

                cover_name = os.path.splitext(os.path.basename(song_path))[0] + ".webp"
                cover_path = os.path.join(COVERS_DIR, cover_name)

                if not (ui.show_covers_enabled and os.path.exists(cover_path)):
                    return None

                original = QPixmap(cover_path)
                if original.isNull():
                    return None

                # масштабуємо так, щоб покрити весь квадрат W×H
                s = max(w / original.width(), h / original.height())
                scaled_w = int(original.width() * s)
                scaled_h = int(original.height() * s)
                scaled = original.scaled(
                    scaled_w, scaled_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

                # центр + ручний зсув по X
                center_left = (scaled_w - w) // 2
                left = center_left + int(shift_x)
                left = max(0, min(left, max(0, scaled_w - w)))
                top = (scaled_h - h) // 2
                top = max(0, min(top, max(0, scaled_h - h)))

                out = QPixmap(w, h)
                out.fill(Qt.transparent)
                p = QPainter(out)
                p.setRenderHint(QPainter.Antialiasing, True)
                path = QPainterPath()
                path.addRoundedRect(0, 0, w, h, radius, radius)
                p.setClipPath(path)
                # зсуваємо реальне фото вліво на left
                p.drawPixmap(-left, -top, scaled)
                p.end()
                return out
            except Exception:
                return None

        # ---------- Вікно Big Picture ----------
        class BigPictureWindow(QMainWindow):
            def __init__(self, ui):
                super().__init__()
                self.ui = ui
                self.setWindowTitle("PyFy Big Picture")
                self.setWindowFlags(Qt.FramelessWindowHint)

                # фон-анімація
                self._ready = False
                self.DENSITY_DIVISOR = 15000
                self.R_MIN = 350
                self.R_MAX = 840
                self.SPEED_MIN = 0.6
                self.SPEED_MAX = 1.8
                self.H_MIN, self.H_MAX = 0, 359
                self.S_MIN, self.S_MAX = 200, 255
                self.V_MIN, self.V_MAX = 210, 255
                self.ALPHA_CENTER = 100
                self.ALPHA_EDGE = 0
                self._build_points()

                central = QWidget(self)
                self.setCentralWidget(central)

                # === Головний вертикальний контейнер (його ще НЕМА у твоєму коді) ===
                main_vbox = QVBoxLayout(central)
                main_vbox.setContentsMargins(0, 0, 0, 0)
                main_vbox.setSpacing(0)

                # ======= ВЕРХНЄ ПОЛЕ ВВОДУ URL =======
                self.url_input_bp = QLineEdit()
                self.url_input_bp.setPlaceholderText("Enter YouTube URL…")
                self.url_input_bp.setFixedWidth(480)
                self.url_input_bp.setFixedHeight(40)
                self.url_input_bp.setStyleSheet(
                    """
                    QLineEdit {
                        background: rgba(43,43,44,0.20);
                        border: 1px solid rgba(255,255,255,0.23);
                        border-radius: 16px;
                        color: white;
                        padding-left: 14px;
                        font-size: 15px;
                    }
                """
                )
                self.url_input_bp.returnPressed.connect(
                    lambda: self.ui.download_from_youtube_bigpicture(
                        self.url_input_bp.text()
                    )
                )

                top_bar = QHBoxLayout()
                top_bar.setContentsMargins(0, 20, 0, 10)
                top_bar.setAlignment(Qt.AlignHCenter)
                top_bar.addWidget(self.url_input_bp)

                # Додаємо верхній бар у основний вертикальний layout
                main_vbox.addLayout(top_bar)

                # === ТЕПЕР СТВОРЮЄМО ROOT ДЛЯ ВСЬОГО ІНШОГО ===
                root = QHBoxLayout()
                main_vbox.addLayout(root)

                root.setContentsMargins(0, 0, 0, 0)
                root.setSpacing(0)

                # ========== ЛІВА ПАНЕЛЬ ==========
                left = QFrame()
                left.setStyleSheet("QFrame { background: transparent; }")
                left_lo = QVBoxLayout(left)
                left_lo.setContentsMargins(20, 30, 24, 30)
                left_lo.setSpacing(12)

                # Обкладинка
                self.cover_lbl = QLabel(central)
                self.cover_lbl.setFixedSize(COVER_SIZE, COVER_SIZE)
                self.cover_lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.cover_lbl.setStyleSheet("QLabel { background: transparent; }")
                self.cover_lbl.move(20, 20)

                cov = load_rounded_cover_with_shift(
                    self.ui,
                    COVER_SIZE,
                    COVER_SIZE,
                    COVER_RADIUS,
                    shift_x=COVER_IMAGE_SHIFT,
                )
                if cov:
                    self.cover_lbl.setPixmap(cov)
                else:
                    ph = QPixmap(COVER_SIZE, COVER_SIZE)
                    ph.fill(Qt.transparent)
                    p = QPainter(ph)
                    p.setRenderHint(QPainter.Antialiasing, True)
                    path = QPainterPath()
                    path.addRoundedRect(
                        0, 0, COVER_SIZE, COVER_SIZE, COVER_RADIUS, COVER_RADIUS
                    )
                    p.setClipPath(path)
                    p.fillRect(0, 0, COVER_SIZE, COVER_SIZE, QColor(255, 255, 255, 22))
                    f = QFont()
                    f.setPointSize(120)
                    p.setFont(f)
                    p.setPen(Qt.white)
                    p.drawText(ph.rect(), Qt.AlignCenter, "🎵")
                    p.end()
                    self.cover_lbl.setPixmap(ph)

                # Назва треку з контуром
                self.title_lbl = OutlineLabel("", outline=2)
                f = QFont()
                f.setPointSize(34)
                f.setBold(True)
                self.title_lbl.setFont(f)
                self.title_lbl.setFixedHeight(48)
                self._update_title()
                self.title_lbl = OutlineLabel("", outline=2, parent=central)
                f = QFont()
                f.setPointSize(34)
                f.setBold(True)
                self.title_lbl.setFont(f)
                self.title_lbl.adjustSize()

                # фіксована позиція тексту
                self.title_lbl.move(
                    20, COVER_SIZE + 30
                )  # ← X=40, Y=позиція під обкладинкою
                self.title_lbl.show()

                self._update_title()

                # трохи відпускаємо вниз
                left_lo.addStretch(1)

                # МАЛИЙ BOX ПЛЕЙЛІСТІВ ЗЛІВА (як список пісень)
                self.playlists_small = QListWidget()
                self.playlists_small.setFixedHeight(280)
                self.playlists_small.setFixedWidth(260)
                self.playlists_small.setStyleSheet(
                    "QListWidget { background: rgba(255,255,255,0.05); "
                    "border: 1px solid rgba(255,255,255,0.10); "
                    "border-radius: 12px; }"
                )
                self.playlists_small.setItemDelegate(
                    OutlineItemDelegate(self.playlists_small, outline=1.6)
                )

                for name in self.ui.playlists.keys():
                    self.playlists_small.addItem(QListWidgetItem(name))

                def on_pick_playlist(item):
                    name = item.text()
                    paths = self.ui.playlists.get(name, [])
                    self._paths = list(paths)
                    self.tracks_list.clear()
                    for pth in self._paths:
                        self.tracks_list.addItem(
                            QListWidgetItem(os.path.splitext(os.path.basename(pth))[0])
                        )
                    # синхронізуємо поточний плейліст у основному UI
                    self.ui.current_playlist_name = name
                    self.ui.current_playlist = list(paths)

                self.playlists_small.itemClicked.connect(on_pick_playlist)
                left_lo.addWidget(self.playlists_small)

                # Прогрес трохи нижче середини
                self.progress = QSlider(Qt.Horizontal)
                self.progress.setRange(0, 0)
                self.progress.setFixedWidth(260)
                self.progress.setStyleSheet(
                    """
                    QSlider::groove:horizontal {
                        height: 10px;
                        background: rgba(255,255,255,0.20);
                        border-radius: 8px;
                    }
                    QSlider::handle:horizontal {
                        background: #4a9eff;
                        width: 18px;
                        height: 18px;
                        margin: -6px 0;
                        border-radius: 9px;
                    }
                    QSlider::sub-page:horizontal {
                        background: #4a9eff;
                        border-radius: 8px;
                    }
                """
                )
                self.progress.sliderMoved.connect(
                    lambda v: self.ui.player.setPosition(v)
                )
                left_lo.addWidget(self.progress)

                # Гучність
                self.volume = QSlider(Qt.Horizontal)
                self.volume.setRange(0, 100)
                self.volume.setFixedWidth(260)
                self.volume.setValue(self.ui.player.volume())
                self.volume.valueChanged.connect(self.ui.player.setVolume)
                self.volume.valueChanged.connect(self.ui.save_volume)
                self.volume.setStyleSheet(
                    """
                    QSlider::groove:horizontal {
                        height: 8px;
                        background: rgba(255,255,255,0.14);
                        border-radius: 6px;
                    }
                    QSlider::handle:horizontal {
                        background: rgba(255,255,255,0.90);
                        width: 14px;
                        height: 14px;
                        margin: -5px 0;
                        border-radius: 7px;
                    }
                    QSlider::sub-page:horizontal {
                        background: rgba(255,255,255,0.45);
                        border-radius: 6px;
                    }
                """
                )
                left_lo.addWidget(self.volume)

                # Кнопки керування в «скляному» боксі
                glass = QFrame()
                glass.setStyleSheet(
                    """
                    QFrame {
                        background: rgba(255,255,255,0.10);
                        border: 1px solid rgba(255,255,255,0.18);
                        border-radius: 18px;
                    }
                """
                )
                glass_lo = QHBoxLayout(glass)
                glass_lo.setContentsMargins(14, 10, 14, 10)
                glass_lo.setSpacing(10)

                def mk_btn(txt, cb):
                    b = QPushButton(txt)
                    b.setFixedSize(72, 44)
                    b.setCursor(Qt.PointingHandCursor)
                    b.setStyleSheet(
                        """
                        QPushButton {
                            background: rgba(20,20,20,0.15);
                            border: 1px solid rgba(255,255,255,0.12);
                            color: #fff;
                            border-radius: 12px;
                            font-size: 18px;
                        }
                        QPushButton:hover { background: rgba(20,20,20,0.25); }
                        QPushButton:pressed { background: rgba(20,20,20,0.32); }
                    """
                    )
                    b.clicked.connect(cb)
                    return b

                prev_btn = mk_btn("⏮", self.ui._play_prev)
                play_btn = mk_btn("▶", self.ui._toggle_play)
                next_btn = mk_btn("⏭", self.ui._play_next)
                self.repeat_btn = mk_btn("🔁", self._toggle_repeat)  # ← НОВА КНОПКА

                glass_lo.addWidget(prev_btn)
                glass_lo.addWidget(play_btn)
                glass_lo.addWidget(next_btn)
                glass_lo.addWidget(self.repeat_btn)  # ← ДОДАЄМО В LAYOUT

                left_lo.addWidget(glass, 0, alignment=Qt.AlignLeft)

                # ========== ПРАВА ПАНЕЛЬ (СПИСОК ПІСЕНЬ) ==========
                right = QFrame()
                right.setFixedWidth(RIGHT_PANEL_WIDTH)
                right.setStyleSheet(
                    """
                    QFrame {
                        background: rgba(255,255,255,0.08);
                        border: 1px solid rgba(255,255,255,0.12);
                        border-top-left-radius: 16px;
                        border-bottom-left-radius: 16px;
                    }
                """
                )
                rlo = QVBoxLayout(right)
                rlo.setContentsMargins(16, 20, 16, 24)
                rlo.setSpacing(10)

                # без надпису "Tracks" — як ти просив
                self.tracks_list = QListWidget()
                self.tracks_list.setStyleSheet(
                    "QListWidget { background: transparent; border: none; }"
                )
                self.tracks_list.setItemDelegate(
                    OutlineItemDelegate(self.tracks_list, outline=1.6)
                )

                # початкові треки: беремо з playback_playlist / current_playlist / All Songs
                base_pl = (
                    self.ui.playback_playlist
                    or self.ui.current_playlist
                    or self.ui.playlists.get(self.ui.current_playlist_name or "", [])
                    or self.ui.playlists.get("All Songs", [])
                )
                self._paths = list(base_pl)

                for pth in self._paths:
                    item = QListWidgetItem(os.path.splitext(os.path.basename(pth))[0])
                    item.setSizeHint(QSize(0, 56))
                    self.tracks_list.addItem(item)

                def play_item(it):
                    idx = self.tracks_list.row(it)
                    self.ui.current_playlist = list(self._paths)
                    self.ui.play_song(idx)
                    # оновити титул + обкладинку
                    self._update_title()
                    upd = load_rounded_cover_with_shift(
                        self.ui,
                        COVER_SIZE,
                        COVER_SIZE,
                        COVER_RADIUS,
                        shift_x=COVER_IMAGE_SHIFT,
                    )
                    if upd:
                        self.cover_lbl.setPixmap(upd)

                self.tracks_list.itemDoubleClicked.connect(play_item)
                rlo.addWidget(self.tracks_list, 1)

                # зібрати
                root.addWidget(left, 1)
                root.addWidget(right, 0)

                # таймер і сигнали
                self.timer = QTimer(self)
                self.timer.timeout.connect(self._tick)
                self.timer.start(16)

                self.ui.player.positionChanged.connect(self._on_pos)
                self.ui.player.durationChanged.connect(self._on_dur)

                self._ready = True
                self.showFullScreen()

            def _toggle_repeat(self):
                # Ініціалізуємо режим, якщо його немає
                if not hasattr(self.ui, "repeat_mode"):
                    self.ui.repeat_mode = "off"

                # Цикл: OFF → ALL → ONE → OFF
                if self.ui.repeat_mode == "off":
                    self.ui.repeat_mode = "all"
                    self.repeat_btn.setText("🔁")
                    self.repeat_btn.setStyleSheet(
                        """
                        QPushButton {
                            background: rgba(74,158,255,0.35);
                            border: 1px solid rgba(74,158,255,0.60);
                            color: #fff;
                            border-radius: 12px;
                            font-size: 18px;
                        }
                        QPushButton:hover { background: rgba(74,158,255,0.45); }
                        QPushButton:pressed { background: rgba(74,158,255,0.55); }
                    """
                    )
                elif self.ui.repeat_mode == "all":
                    self.ui.repeat_mode = "one"
                    self.repeat_btn.setText("🔂")
                    # Залишаємо синій стиль
                else:
                    self.ui.repeat_mode = "off"
                    self.repeat_btn.setText("🔁")
                    self.repeat_btn.setStyleSheet(
                        """
                        QPushButton {
                            background: rgba(20,20,20,0.15);
                            border: 1px solid rgba(255,255,255,0.12);
                            color: #fff;
                            border-radius: 12px;
                            font-size: 18px;
                        }
                        QPushButton:hover { background: rgba(20,20,20,0.25); }
                        QPushButton:pressed { background: rgba(20,20,20,0.32); }
                    """
                    )

            def _update_title(self):
                try:
                    title = self.ui._current_song_title()
                except Exception:
                    title = "Unknown"
                self.title_lbl.setText(title)
                self.title_lbl.adjustSize()

            def _on_pos(self, ms):
                self.progress.blockSignals(True)
                self.progress.setValue(ms)
                self.progress.blockSignals(False)

            def _on_dur(self, ms):
                self.progress.setRange(0, ms or 0)

            # фон-анімація (логіка як була)
            def _build_points(self):
                w, h = max(1, self.width()), max(1, self.height())
                target_count = max(28, int((w * h) / self.DENSITY_DIVISOR))
                self.points = []
                inframe_count = int(target_count * 0.45)
                top_count = target_count - inframe_count
                for _ in range(inframe_count):
                    self.points.append(self._new_point(mode="inframe"))
                for _ in range(top_count):
                    self.points.append(self._new_point(mode="prefall"))

            def _rand_bright_color(self):
                h = randint(self.H_MIN, self.H_MAX)
                s = randint(self.S_MIN, self.S_MAX)
                v = randint(self.V_MIN, self.V_MAX)
                return QColor.fromHsv(h, s, v, self.ALPHA_CENTER)

            def _new_point(self, mode="prefall"):
                w, h = self.width(), self.height()
                r = randint(self.R_MIN, self.R_MAX)
                x = randint(-int(self.R_MAX * 1), w + int(self.R_MAX * 1))
                vy = uniform(self.SPEED_MIN, self.SPEED_MAX)
                color = self._rand_bright_color()

                if mode == "inframe":
                    y = uniform(0, h)
                else:
                    start_above = r + int(h * 0.35)
                    pre_distance = uniform(0, h * 0.40)
                    y = -(start_above - pre_distance)
                    y = y if y <= -r else -r

                return [x, float(y), r, vy, color]

            def _tick(self):
                w, h = self.width(), self.height()
                for p in self.points:
                    p[1] += p[3]
                    if p[1] - p[2] > h:
                        p[0] = randint(-int(self.R_MAX * 1), w + int(self.R_MAX * 1))
                        p[2] = randint(self.R_MIN, self.R_MAX)
                        p[3] = uniform(self.SPEED_MIN, self.SPEED_MAX)
                        p[4] = self._rand_bright_color()
                        start_above = p[2] + int(h * 0.35)
                        pre_distance = uniform(0, h * 0.40)
                        y = -(start_above - pre_distance)
                        p[1] = y if y <= -p[2] else -p[2]
                self.update()

            def resizeEvent(self, e):
                if getattr(self, "_ready", False):
                    self._build_points()
                return super().resizeEvent(e)

            def paintEvent(self, event):
                p = QPainter(self)
                p.setRenderHint(QPainter.Antialiasing, True)
                p.fillRect(self.rect(), QColor(12, 14, 26))
                p.setCompositionMode(QPainter.CompositionMode_Screen)

                for x, y, r, vy, color in self.points:
                    grad = QRadialGradient(float(x), float(y), float(r))
                    c_center = QColor(color)
                    c_edge = QColor(
                        color.red(), color.green(), color.blue(), self.ALPHA_EDGE
                    )
                    grad.setColorAt(0.0, c_center)
                    grad.setColorAt(1.0, c_edge)
                    p.setBrush(grad)
                    p.setPen(Qt.NoPen)
                    rect = QRectF(
                        float(x - r), float(y - r), float(r * 2), float(r * 2)
                    )
                    p.drawEllipse(rect)

            def keyPressEvent(self, e):
                if e.key() == Qt.Key_Escape:
                    self.close()
                    self.ui.show()

        # --- запуск ---
        self.hide()
        self.big_picture_window = BigPictureWindow(self)
        self.big_picture_window.show()

    def check_for_updates(self):
        """_current_song_title"""
        try:
            latest = get_latest_version()
            if latest is None:
                return

            cmp = compare_versions(VERSION, latest)
            if cmp < 0:  # текущая версия меньше последней
                logger.info(
                    "[Update] New version available: %s (current: %s)", latest, VERSION
                )
                if self.topbar.update_btn:
                    self.topbar.update_btn.show()
            else:
                logger.debug("[Update] Current version is up-to-date: %s", VERSION)
                if self.topbar.update_btn:
                    self.topbar.update_btn.hide()
        except Exception as e:
            logger.exception(f"[Ошибка] check_for_updates: {e}")

    def start_update_process(self):
        update_path = os.path.join(os.path.dirname(get_current_path()), "Update.exe")
        if os.path.exists(update_path):
            subprocess.Popen([update_path])
        QApplication.exit(0)
