from __future__ import unicode_literals
import sys
import os
import json
import yt_dlp as youtube_dl
from PIL import Image
from pypresence import Presence
import threading
import time
import subprocess
import shutil
import urllib.request
from PyQt5.QtCore import (
    Qt,
    QUrl,
    QTime,
    QPoint,
    QObject,
    QEvent,
    QSize,
    QRectF,
    QTimer,
    QThread,
    pyqtSignal,
)
from PyQt5.QtGui import QColor, QIcon, QPixmap, QPainterPath, QRegion, QPainter
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QFrame,
    QGraphicsDropShadowEffect,
    QFileDialog,
    QSlider,
    QListWidgetItem,
    QInputDialog,
    QMenu,
    QSizePolicy,
    QLineEdit,
    QCheckBox,
    QMessageBox,
    QComboBox,
    QDialog,
    QProgressBar,
)
import logging
from pyfy_utils import sanitize_filename

# lightweight logger; detailed handlers (file) will be added after config dir is available
logger = logging.getLogger("PyFy")
logger.addHandler(logging.NullHandler())
VERSION = "1.3.11"
VERSION_URL = "https://raw.githubusercontent.com/PykHubOfficial/Testmain/refs/heads/main/versionPyFy.txt"
I18N = {
    "en": {
        "settings_title": "Settings",
        "tab_interface": "Interface",
        "tab_other": "Other",
        "interface_title": "Interface Settings",
        "show_covers": "Show album covers",
        "language": "Language",
        "lang_en": "English",
        "lang_uk": "Ukrainian",
        "lang_ru": "Russian",
        "other_title": "Other",
        "rpc_checkbox_en": "Show as Discord status",
        "drv_text": 'Music not playing? <a href="{url}">Download Driver</a>',
        "icons_text": "Missing some icons? <a href='#'>Download all</a>",
        "downloading": "Downloading...",
        "download_done": "Download finished",
        "download_fail": "Download failed",
        "enter_big_picture": "Enter Big Picture Mode (Bugs - Unready)",
        "app_title": "PyFy Music Player",
        "url_placeholder": "Enter YouTube URL...",
        "update_ready_tooltip": "Update is ready!",
        "playlists": "Playlists",
        "liked_btn": "❤️ Liked",
        "empty_placeholder": 'Find songs via "+ Add Songs" or put tracks into local/data/Songs',
        "add_songs": "+ Add Songs",
        "add_folder": "+ Add Folder",
        "create_playlist": "Create Playlist",
        "rescan": "Rescan Songs",
        "restart": "Restart",
        "open_songs_dir": "Open Songs Dir",
        "menu_create_playlist": "Create playlist",
        "menu_rename": "✏ Rename",
        "menu_delete": "🗑 Delete",
        "dlg_rename_title": "Rename playlist",
        "dlg_rename_prompt": "New name:",
        "dlg_new_playlist_title": "Create playlist",
        "dlg_new_playlist_prompt": "Playlist name:",
        "filedlg_select_songs": "Select Songs",
        "filedlg_select_folder": "Select folder",
        "filedlg_audio_filter": "Audio Files (*.mp3 *.wav *.flac *.m4a *.aac *.mp4 *.webm)",
        "msg_downloading_title": "Downloading",
        "msg_downloading_text": "Downloading Audio...",
        "msg_error_title": "Error",
        "msg_error_download_text": "Failed to download audio",
        "msg_error_download_hint": """Make sure the URL is correct and you have an internet connection.
Try this url format:
https://www.youtube.com/watch?v=1234567890
If the problem persists, please report it on Discord im.pyk""",
    },
    "uk": {
        "settings_title": "Налаштування",
        "tab_interface": "Інтерфейс",
        "tab_other": "Інше",
        "interface_title": "Налаштування інтерфейсу",
        "show_covers": "Показувати обкладинки альбомів",
        "language": "Мова",
        "lang_en": "Англійська",
        "lang_uk": "Українська",
        "lang_ru": "Російська",
        "other_title": "Інше",
        "rpc_checkbox_en": "Show as Discord status",
        "drv_text": 'Не відтворюється музика? <a href="{url}">Завантажити драйвер</a>',
        "icons_text": "Немає деяких значків? <a href='#'>Завантажити все</a>",
        "downloading": "Завантаження...",
        "download_done": "Завантаження завершено",
        "download_fail": "Помилка завантаження",
        "enter_big_picture": "Увійти в режим Big Picture (Bugs - Unready)",
        "app_title": "PyFy Музичний плеєр",
        "url_placeholder": "Введіть посилання YouTube...",
        "update_ready_tooltip": "Доступне оновлення!",
        "playlists": "Плейлисти",
        "liked_btn": "❤️ Вибране",
        "empty_placeholder": 'Знайдіть пісні через "+ Додати пісні" або покладіть треки в local/data/Songs',
        "add_songs": "+ Додати пісні",
        "add_folder": "+ Додати теку",
        "create_playlist": "Створити плейлист",
        "rescan": "Пересканувати пісні",
        "restart": "Перезапустити",
        "open_songs_dir": "Відкрити теку пісень",
        "menu_create_playlist": "Створити плейлист",
        "menu_rename": "✏ Перейменувати",
        "menu_delete": "🗑 Видалити",
        "dlg_rename_title": "Перейменування плейлиста",
        "dlg_rename_prompt": "Нова назва:",
        "dlg_new_playlist_title": "Створення плейлиста",
        "dlg_new_playlist_prompt": "Назва плейлиста:",
        "filedlg_select_songs": "Вибір пісень",
        "filedlg_select_folder": "Вибір теки",
        "filedlg_audio_filter": "Аудіо файли (*.mp3 *.wav *.flac *.m4a *.aac *.mp4 *.webm)",
        "msg_downloading_title": "Завантаження",
        "msg_downloading_text": "Завантаження аудіо...",
        "msg_error_title": "Помилка",
        "msg_error_download_text": "Не вдалося завантажити аудіо",
        "msg_error_download_hint": """Переконайтеся, що посилання правильне і є інтернет-з'єднання.
Приклад посилання:
https://www.youtube.com/watch?v=1234567890
Якщо проблема не зникає, напишіть у Discord im.pyk""",
    },
    "ru": {
        "settings_title": "Настройки",
        "tab_interface": "Интерфейс",
        "tab_other": "Другое",
        "interface_title": "Настройки интерфейса",
        "show_covers": "Показывать обложки альбомов",
        "language": "Язык",
        "lang_en": "Английский",
        "lang_uk": "Украинский",
        "lang_ru": "Русский",
        "other_title": "Другое",
        "rpc_checkbox_en": "Show as Discord status",
        "drv_text": 'Не воспроизводится музыка? <a href="{url}">Скачать драйвер</a>',
        "icons_text": "Нет некоторых значков? <a href='#'>Скачать всё</a>",
        "downloading": "Загрузка...",
        "download_done": "Загрузка завершена",
        "download_fail": "Ошибка загрузки",
        "enter_big_picture": "Войти в режим Big Picture (Bugs - Unready)",
        "app_title": "PyFy Музыкальный плеер",
        "url_placeholder": "Введите ссылку YouTube...",
        "update_ready_tooltip": "Доступно обновление!",
        "playlists": "Плейлисты",
        "liked_btn": "❤️ Избранное",
        "empty_placeholder": 'Найдите песни через "+ Добавить песни" или положите треки в local/data/Songs',
        "add_songs": "+ Добавить песни",
        "add_folder": "+ Добавить папку",
        "create_playlist": "Создать плейлист",
        "rescan": "Пересканировать песни",
        "restart": "Перезапустить",
        "open_songs_dir": "Открыть папку с песнями",
        "menu_create_playlist": "Создать плейлист",
        "menu_rename": "✏ Переименовать",
        "menu_delete": "🗑 Удалить",
        "dlg_rename_title": "Переименование плейлиста",
        "dlg_rename_prompt": "Новое имя:",
        "dlg_new_playlist_title": "Создание плейлиста",
        "dlg_new_playlist_prompt": "Название плейлиста:",
        "filedlg_select_songs": "Выбор песен",
        "filedlg_select_folder": "Выбор папки",
        "filedlg_audio_filter": "Аудио файлы (*.mp3 *.wav *.flac *.m4a *.aac *.mp4 *.webm)",
        "msg_downloading_title": "Загрузка",
        "msg_downloading_text": "Загрузка аудио...",
        "msg_error_title": "Ошибка",
        "msg_error_download_text": "Не удалось загрузить аудио",
        "msg_error_download_hint": """Убедитесь, что ссылка правильная и есть интернет.
Пример ссылки:
https://www.youtube.com/watch?v=1234567890
        Если проблема не исчезает, сообщите в Discord im.pyk""",
    },
}
# ---------------------------
# Version check helpers


def compare_versions(v1: str, v2: str) -> int:
    """Compare two semantic version strings.

    Returns:
        -1 if v1 < v2
         0 if equal
         1 if v1 > v2
    """
    try:
        a = [int(x) for x in str(v1).split(".")]
        b = [int(x) for x in str(v2).split(".")]
        length = max(len(a), len(b))
        a += [0] * (length - len(a))
        b += [0] * (length - len(b))
        for x, y in zip(a, b):
            if x < y:
                return -1
            if x > y:
                return 1
        return 0
    except Exception:
        return 0


def get_latest_version():
    """Получает последнюю версию с сервера."""
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=6) as resp:
            return resp.read().decode("utf-8").strip().splitlines()[0].strip()
    except Exception as e:
        logger.exception(f"[Ошибка] Не удалось получить последнюю версию: {e}")
        return None


# ---------------------------
# Config paths
# ---------------------------
def get_current_path():
    if getattr(sys, "frozen", False):  # если запущено как .exe (PyInstaller и т.п.)
        return os.path.dirname(sys.executable)
    else:  # если обычный .py
        return os.path.dirname(os.path.abspath(__file__))


LAV_FILTERS_URL = "https://github.com/Nevcairiel/LAVFilters/releases/"
LAV_FILTERS_DIRECT = ""
ICONS_PACK_ZIP = (
    "https://github.com/PykHubOfficial/Testmain/raw/refs/heads/main/icons_pack.zip"
)
CONFIG_DIR1 = os.path.join("local", "cfg")
SONGS_DIR1 = os.path.join("local", "data", "Songs")
SONGS_DIR = os.path.join(get_current_path(), SONGS_DIR1)
CONFIG_DIR = os.path.join(get_current_path(), CONFIG_DIR1)
ICON1 = os.path.dirname(get_current_path())
ICON = os.path.join(ICON1, "app.ico")
LAST_PLAYLIST_FILE = os.path.join(CONFIG_DIR, "last_playlist.json")
logger.debug("SONGS_DIR=%s CONFIG_DIR=%s", SONGS_DIR, CONFIG_DIR)


# ---------------------------
# Helpers (filesystem & downloads)
# ---------------------------
def ensure_dir(path: str):
    try:
        if os.path.exists(path) and os.path.isfile(path):
            os.remove(path)
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        logger.exception(f"[ensure_dir] {path}: {e}")


def download_file(url: str, dst_path: str) -> bool:
    try:
        parent = os.path.dirname(dst_path)
        ensure_dir(parent)
        with urllib.request.urlopen(url, timeout=30) as resp, open(
            dst_path, "wb"
        ) as out:
            out.write(resp.read())
        return True
    except Exception as e:
        logger.exception(f"[download_file] {url} -> {dst_path}: {e}")
        return False


LIKED_FILE = os.path.join(CONFIG_DIR, "liked.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")
VOLUME_FILE = os.path.join(CONFIG_DIR, "volume.json")
PLAYLISTS_FILE = os.path.join(CONFIG_DIR, "playlists.json")
ICONS_DIR1 = os.path.join("local", "data", "imgs")
ICONS_DIR = os.path.join(get_current_path(), ICONS_DIR1)
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
downloadimg_path = os.path.join(os.path.dirname(get_current_path()), "download.png")
logger.debug("downloadimg_path: %s", downloadimg_path)
ensure_dir(ICONS_DIR)
if os.path.exists(downloadimg_path):
    shutil.move(downloadimg_path, ICONS_DIR)
downloadupdate_path = os.path.join(
    os.path.dirname(get_current_path()), "downloadupdate.png"
)
logger.debug("downloadupdate_path: %s", downloadupdate_path)
if os.path.exists(downloadupdate_path):
    shutil.move(downloadupdate_path, ICONS_DIR)
COVERS_DIR1 = os.path.join("local", "data", "Covers")
COVERS_DIR = os.path.join(get_current_path(), COVERS_DIR1)
logger.debug("ICONS_DIR: %s", ICONS_DIR)
ensure_dir(CONFIG_DIR)
# Setup file logging now that CONFIG_DIR exists
try:
    import logging.handlers

    log_file = os.path.join(CONFIG_DIR, "pyfy.log")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    # avoid adding multiple file handlers
    if not any(
        isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers
    ):
        logger.addHandler(fh)
except Exception:
    logger.exception("Failed to set up file logging")
ensure_dir(SONGS_DIR)


def audio_download(url_video_youtube: str, progress_hook=None, cancel_check=None):
    ensure_dir(SONGS_DIR)
    ensure_dir(COVERS_DIR)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(SONGS_DIR, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "writethumbnail": True,
    }
    tmp_files = set()

    def _wrap_hook(d):
        fn = d.get("filename") or d.get("tmpfilename") or d.get("filepath")
        if fn:
            try:
                tmp_files.add(os.path.abspath(fn))
            except Exception:
                pass
        if progress_hook:
            progress_hook(d)

    if progress_hook:
        ydl_opts["progress_hooks"] = [_wrap_hook]

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url_video_youtube, download=True)

            # allow cancellation check after extraction
            if cancel_check and cancel_check():
                raise Exception("Download cancelled")

            audio_title = sanitize_filename(info_dict.get("title", "audio"))
            audio_time_line = info_dict.get("chapters", None)
            webp_path = os.path.join(SONGS_DIR, f"{audio_title}.webp")
            cover_path = None

            if os.path.exists(webp_path):
                cover_path = os.path.join(COVERS_DIR, f"{audio_title}.webp")
                if os.path.exists(cover_path):
                    os.remove(cover_path)

                # Переносим webp
                shutil.move(webp_path, cover_path)
                logger.info("Cover moved to: %s", cover_path)
            else:
                logger.warning("WebP cover not found after download.")

            logger.info("Download audio successful: %s", audio_title)

        file_name = os.path.join(SONGS_DIR, f"{audio_title}.mp3")
        return file_name, audio_title, audio_time_line, cover_path
    except Exception:
        try:
            from pyfy_utils import remove_files_if_exist

            remove_files_if_exist(tmp_files)
        except Exception:
            logger.exception("Error cleaning up partial files")
        raise


# ---------------------------
class CustomInputDialog(QWidget):
    def __init__(self, title="Input", label="Enter text:", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 200)  # немного больше окно

        container = QFrame(self)
        container.setStyleSheet(
            """
            QFrame {
                background-color: #252426;
                border-radius: 12px;
                border: 1px solid #3a3a3b;
            }
        """
        )
        container.setGeometry(0, 0, 400, 200)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # кастомная шапка
        self.topbar = ModernTopBar(self)
        layout.addWidget(self.topbar)

        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        body.setSpacing(14)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: white; font-size: 16px; font-weight: 500;")
        body.addWidget(lbl)

        self.edit = QLineEdit()
        self.edit.setStyleSheet(
            """
            QLineEdit {
                background: #1c1c1d;
                border: 1px solid #3a3a3b;
                border-radius: 8px;
                color: white;
                font-size: 15px;
                padding: 10px 12px;
            }
        """
        )
        """self._connect_signals()"""
        self.edit.setMinimumHeight(38)
        body.addWidget(self.edit)

        buttons = QHBoxLayout()
        ok_btn = AnimatedButton("OK", "secondary")
        cancel_btn = AnimatedButton("Cancel", "secondary")

        # увеличим кнопки
        ok_btn.setFixedHeight(36)
        cancel_btn.setFixedHeight(36)
        ok_btn.setMinimumWidth(100)
        cancel_btn.setMinimumWidth(100)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        body.addLayout(buttons)

        layout.addLayout(body)
        self.result = None

    def accept(self):
        self.result = self.edit.text()
        self.close()

    def reject(self):
        self.result = None
        self.close()

    @staticmethod
    def getText(parent, title, label):
        dlg = CustomInputDialog(title, label, parent)
        dlg.show()
        loop = QApplication.instance()
        while dlg.isVisible():
            loop.processEvents()
        return dlg.result, dlg.result is not None


# ---------------------------
# Small reusable button
# ---------------------------
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


# ---------------------------
# Top bar
# ---------------------------
class ClickFilter(QObject):
    def __init__(self, line_edit):
        super().__init__()
        self.line_edit = line_edit

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if self.line_edit.hasFocus() and obj != self.line_edit:
                self.line_edit.clearFocus()
        return super().eventFilter(obj, event)


class ModernTopBar(QFrame):
    def _t(self, key: str) -> str:
        # Берём перевод из родителя (MusicPlayerUI)
        lang = getattr(self.parent, "language", "en")
        return I18N.get(lang, I18N["en"]).get(key, key)

    def apply_i18n(self):
        # Локализуем только элементы топбара
        self.title_label.setText(self._t("app_title"))
        self.url_input.setPlaceholderText(self._t("url_placeholder"))
        self.update_btn.setToolTip(self._t("update_ready_tooltip"))

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.startPos = None
        self.setFixedHeight(48)
        self.setStyleSheet(
            """
            QFrame { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(30,30,30,220), stop:1 rgba(20,20,20,200)); 
                     border-top-left-radius:15px; border-top-right-radius:15px; }
        """
        )
        self.update_btn = None  # кнопка обновления
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(8)

        self.title_label = QLabel("PyFy Music Player")
        self.title_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 16px; border: none;"
        )
        layout.addWidget(self.title_label)

        layout.addSpacing(100)

        # Контейнер поиска
        search_container = QHBoxLayout()
        search_container.setSpacing(0)
        search_container.setContentsMargins(0, 0, 0, 0)

        # Текстбокс
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube URL...")
        self.url_input.setFixedWidth(390)
        self.url_input.setFixedHeight(32)
        self.url_input.setStyleSheet(
            """
            QLineEdit {
                background: rgba(43,43,44,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                border-right: none;
                color: white;
                font-size: 13px;
                padding-left: 14px;
                padding-right: 8px;
            }
            QLineEdit:focus {
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.12);
                border-right: none;
            }
        """
        )
        # Не получает фокус при старте, только при клике
        self.url_input.setFocusPolicy(Qt.ClickFocus)

        search_container.addWidget(self.url_input)

        # Кнопка загрузки
        self.download_btn = QPushButton()
        self.download_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "download.png")))
        self.download_btn.setFixedSize(40, 32)
        self.download_btn.setIconSize(QSize(22, 22))
        self.download_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(43,43,44,0.8);
                border: 1px solid rgba(255,255,255,0.12);
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 16px;
                border-bottom-right-radius: 16px;
                border-left: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(43,43,44,0.8);
            }
            QPushButton:pressed {
                background: rgba(86,86,88,1);
            }
        """
        )
        self.download_btn.setFocusPolicy(Qt.NoFocus)
        self.download_btn.clicked.connect(self.parent.download_from_youtube)
        search_container.addWidget(self.download_btn)

        layout.addLayout(search_container)
        layout.addSpacing(10)
        layout.addStretch()

        # Фильтр кликов (чтобы при клике вне поля снимался фокус)
        self.click_filter = ClickFilter(self.url_input)
        QApplication.instance().installEventFilter(self.click_filter)

        # Enter = клик по кнопке
        self.url_input.returnPressed.connect(self.download_btn.click)

        # Кнопка обновления (изначально скрыта)
        self.update_btn = QPushButton()
        self.update_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "downloadupdate.png")))
        self.update_btn.setIconSize(QSize(22, 22))
        self.update_btn.setFixedSize(36, 34)
        self.update_btn.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff88, stop:1 #00cc66);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                color: white;
                padding: 0px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ffaa, stop:1 #00dd77);
            }
        """
        )
        self.update_btn.setFocusPolicy(Qt.NoFocus)
        self.update_btn.setToolTip(
            I18N.get(getattr(self, "language", "en"), I18N["en"]).get(
                "update_ready_tooltip", "Update is ready!"
            )
        )
        self.update_btn.hide()  # изначально скрыта
        self.update_btn.clicked.connect(self.parent.start_update_process)
        layout.addWidget(self.update_btn)

        self.settings_btn = AnimatedButton("⚙", "icon")
        self.settings_btn.setFixedSize(36, 34)
        self.settings_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 8px;
                color: #cfcfcf;
                font-size: 18px;
                padding: 0px;
            }
            QPushButton:hover { 
                background: rgba(255,255,255,0.06); 
                color: white; 
            }
        """
        )
        self.settings_btn.clicked.connect(self.parent.show_settings)
        layout.addWidget(self.settings_btn)

        self.min_btn = AnimatedButton("−", "icon")
        self.min_btn.setFixedSize(36, 34)
        self.min_btn.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.min_btn)

        self.close_btn = AnimatedButton("✕", "icon")
        self.close_btn.setFixedSize(36, 34)
        self.close_btn.clicked.connect(self.parent.close)
        layout.addWidget(self.close_btn)

    # --- Перемещение окна ---
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.startPos = e.globalPos()

    def mouseMoveEvent(self, e):
        if self.startPos:
            delta = e.globalPos() - self.startPos
            self.parent.move(self.parent.pos() + delta)
            self.startPos = e.globalPos()

    def mouseReleaseEvent(self, e):
        self.startPos = None


# ---------------------------
# Song item widget in list
# ---------------------------


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


# ---------------------------
# Settings Window
# ---------------------------
class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ui = parent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 400)

        container = QFrame(self)
        container.setStyleSheet(
            "QFrame { background-color: #252426; border-radius: 12px; border: 1px solid #3a3a3b; }"
        )
        container.setGeometry(0, 0, 600, 400)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Topbar
        self.topbar = QFrame()
        self.topbar.setFixedHeight(48)
        self.topbar.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(30,30,30,220), stop:1 rgba(20,20,20,200)); border-top-left-radius:12px; border-top-right-radius:12px; border-radius: 0px;}"
        )
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(14, 6, 14, 6)
        self.title_lbl = QLabel("Settings")
        self.title_lbl.setObjectName("settings_title_lbl")
        self.title_lbl.setStyleSheet(
            "color: white; font-weight: bold; font-size: 16px; border: none;"
        )
        topbar_layout.addWidget(self.title_lbl)
        topbar_layout.addStretch()
        close_btn = AnimatedButton("✕", "icon")
        close_btn.setFixedSize(36, 34)
        close_btn.clicked.connect(self.close)
        topbar_layout.addWidget(close_btn)
        main_layout.addWidget(self.topbar)

        # Content
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(150)
        sidebar.setStyleSheet(
            "QFrame { background: rgba(0,0,0,0.2); border-right: 1px solid rgba(255,255,255,0.1); border-radius: 0px; }"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 15, 10, 10)
        sidebar_layout.setSpacing(5)
        self.interface_btn = AnimatedButton("Interface", "secondary")
        self.interface_btn.clicked.connect(self._show_interface_tab)
        sidebar_layout.addWidget(self.interface_btn)
        sidebar_layout.addStretch()
        self.other_btn = AnimatedButton("Other", "secondary")
        self.other_btn.clicked.connect(self._show_other_tab)
        sidebar_layout.addWidget(self.other_btn)
        version_label = QLabel(f"Version {VERSION}")
        version_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px;")
        version_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version_label)
        content.addWidget(sidebar)

        # Right area
        self.settings_content = QFrame()
        self.settings_content.setObjectName("settings_content")
        self.settings_content.setStyleSheet("border-radius: 0px;")
        self.settings_layout = QVBoxLayout(self.settings_content)
        self.settings_layout.setContentsMargins(20, 20, 20, 20)
        self.settings_layout.setSpacing(15)
        content.addWidget(self.settings_content, 1)
        main_layout.addLayout(content)

        # Dragging
        self.startPos = None
        self.topbar.mousePressEvent = self.mousePressEvent
        self.topbar.mouseMoveEvent = self.mouseMoveEvent
        self.topbar.mouseReleaseEvent = self.mouseReleaseEvent

        # Default tab
        self.current_tab = None
        self._show_interface_tab()
        self._apply_i18n_to_settings()

    def _clear_settings_content(self):
        lay = self.settings_layout
        while lay.count():
            it = lay.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
            sub = it.layout()
            if sub:
                while sub.count():
                    si = sub.takeAt(0)
                    if si.widget():
                        si.widget().setParent(None)

    def _activate_tab(self, name: str):
        if name == "interface":
            self.interface_btn.setStyleSheet(
                "QPushButton { background: #4a9eff; border: none; border-radius: 8px; color: white; padding: 10px; text-align: left; }"
            )
            self.other_btn.setStyleSheet(
                "QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: white; padding: 10px; text-align: left; }"
            )
        else:
            self.other_btn.setStyleSheet(
                "QPushButton { background: #4a9eff; border: none; border-radius: 8px; color: white; padding: 10px; text-align: left; }"
            )
            self.interface_btn.setStyleSheet(
                "QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: white; padding: 10px; text-align: left; }"
            )

    def _show_interface_tab(self):
        self.current_tab = "interface"
        self._clear_settings_content()
        self._activate_tab("interface")
        title = QLabel(self._t("interface_title"))
        title.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold; border: none;"
        )
        self.settings_layout.addWidget(title)

        self.show_covers_cb = QCheckBox(self._t("show_covers"))
        self.show_covers_cb.setChecked(
            getattr(self.parent_ui, "show_covers_enabled", True)
        )
        self.show_covers_cb.stateChanged.connect(self._on_toggle_covers)
        self.show_covers_cb.setStyleSheet(
            "QCheckBox { color: white; font-size: 14px; spacing: 8px; } QCheckBox::indicator { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.3); border-radius: 4px; background: rgba(255,255,255,0.05); } QCheckBox::indicator:checked { background: #4a9eff; border-color: #4a9eff; }"
        )
        self.settings_layout.addWidget(self.show_covers_cb)

        from PyQt5.QtWidgets import QComboBox, QHBoxLayout

        row = QHBoxLayout()
        self.lang_label = QLabel(self._t("language"))
        self.lang_label.setStyleSheet("color: white; font-size: 14px; border: none;")
        row.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Українська", "uk")
        self.lang_combo.addItem("Русский", "ru")
        cur = getattr(self.parent_ui, "language", "en")
        idx = {"en": 0, "uk": 1, "ru": 2}.get(cur, 0)
        self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        self.lang_combo.setStyleSheet(
            "QComboBox { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: white; padding: 6px 10px; } QComboBox QAbstractItemView { background: #252426; selection-background-color: #3a3a3b; color: white; }"
        )
        row.addWidget(self.lang_combo, 1)
        row.addStretch()
        self.settings_layout.addLayout(row)

        self.settings_layout.addStretch()
        self._apply_i18n_to_settings()

    def _show_other_tab(self):
        self.current_tab = "other"
        self._clear_settings_content()
        self._activate_tab("other")
        title = QLabel(self._t("other_title"))
        title.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold; border: none;"
        )
        self.settings_layout.addWidget(title)

        self.rpc_cb = QCheckBox("Show as Discord status")
        self.rpc_cb.setChecked(getattr(self.parent_ui, "rpc_enabled", True))
        self.rpc_cb.stateChanged.connect(self._on_toggle_rpc)
        self.rpc_cb.setStyleSheet(
            "QCheckBox { color: white; font-size: 14px; spacing: 8px; } QCheckBox::indicator { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.3); border-radius: 4px; background: rgba(255,255,255,0.05); } QCheckBox::indicator:checked { background: #4a9eff; border-color: #4a9eff; }"
        )
        self.settings_layout.addWidget(self.rpc_cb)

        # Big Picture Mode button
        self.big_picture_btn = AnimatedButton(self._t("enter_big_picture"), "secondary")
        self.big_picture_btn.clicked.connect(self._enter_big_picture_mode)
        self.settings_layout.addWidget(self.big_picture_btn)

        self.lav_label = QLabel()
        self.lav_label.setTextFormat(Qt.RichText)
        self.lav_label.setOpenExternalLinks(True)
        self._update_lav_label()
        self.lav_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 14px;")
        self.settings_layout.addWidget(self.lav_label)

        self.icons_btn = QPushButton()
        self.icons_btn.setCursor(Qt.PointingHandCursor)
        self.icons_btn.setFlat(True)
        self.icons_btn.setStyleSheet(
            "QPushButton { color: #4aa3ff; background: transparent; border: none; text-align: left; font-size: 14px; padding: 0; text-decoration: underline; } QPushButton:hover { color: #77bbff; }"
        )
        self.icons_btn.setText(
            self._t("icons_text").replace("<a href='#'>", "").replace("</a>", "")
        )
        self.icons_btn.clicked.connect(self._download_icons_pack)
        self.settings_layout.addWidget(self.icons_btn)

        self.settings_layout.addStretch()
        self._apply_i18n_to_settings()

    def _t(self, key: str) -> str:
        lang = getattr(self.parent_ui, "language", "en")
        return I18N.get(lang, I18N["en"]).get(key, key)

    def _apply_i18n_to_settings(self):
        t = self._t
        self.title_lbl.setText(t("settings_title"))
        self.interface_btn.setText(t("tab_interface"))
        self.other_btn.setText(t("tab_other"))
        if self.current_tab == "interface":
            if self.settings_layout.count() > 0 and isinstance(
                self.settings_layout.itemAt(0).widget(), QLabel
            ):
                self.settings_layout.itemAt(0).widget().setText(t("interface_title"))
            if hasattr(self, "show_covers_cb"):
                self.show_covers_cb.setText(t("show_covers"))
            if hasattr(self, "lang_label"):
                self.lang_label.setText(t("language"))
        elif self.current_tab == "other":
            if self.settings_layout.count() > 0 and isinstance(
                self.settings_layout.itemAt(0).widget(), QLabel
            ):
                self.settings_layout.itemAt(0).widget().setText(t("other_title"))
            if hasattr(self, "lav_label"):
                self._update_lav_label()
            if hasattr(self, "icons_btn"):
                self.icons_btn.setText(
                    t("icons_text").replace("<a href='#'>", "").replace("</a>", "")
                )
        if hasattr(self.parent_ui, "apply_i18n") and callable(
            self.parent_ui.apply_i18n
        ):
            try:
                self.parent_ui.apply_i18n()
            except Exception as e:
                logger.exception("[apply_i18n hook] %s", e)

    def _enter_big_picture_mode(self):
        self.close()
        self.parent_ui.launch_big_picture_mode()

    def _on_toggle_covers(self, state):
        self.parent_ui.show_covers_enabled = bool(state)
        self.parent_ui.save_settings()
        self.parent_ui.refresh_current_view()

    def _on_lang_changed(self, idx):
        data = self.lang_combo.itemData(idx)
        if not data:
            return
        self.parent_ui.language = data
        self.parent_ui.save_settings()
        if hasattr(self.parent_ui, "apply_i18n"):
            try:
                self.parent_ui.apply_i18n()
            except Exception as e:
                logger.exception("[apply_i18n main] %s", e)
        self._apply_i18n_to_settings()

    def _on_toggle_rpc(self, state):
        enabled = bool(state)
        self.parent_ui.rpc_enabled = enabled
        self.parent_ui.save_settings()
        try:
            if enabled and not self.parent_ui.rpc:
                self.parent_ui.rpc = Presence(self.parent_ui.discord_client_id)
                self.parent_ui.rpc.connect()
            elif not enabled and self.parent_ui.rpc:
                try:
                    self.parent_ui.rpc.clear()
                except Exception:
                    pass
                self.parent_ui.rpc_running = False
                self.parent_ui.rpc = None
        except Exception as e:
            logger.exception("[Discord RPC Toggle Error] %s", e)

    def _update_lav_label(self):
        url = LAV_FILTERS_DIRECT if LAV_FILTERS_DIRECT else LAV_FILTERS_URL
        self.lav_label.setText(self._t("drv_text").format(url=url))

    def _download_icons_pack(self):
        if not ICONS_PACK_ZIP:
            QMessageBox.information(
                self, self._t("download_fail"), "ICONS_PACK_ZIP is not set in code."
            )
            return
        try:
            QMessageBox.information(
                self, self._t("downloading"), self._t("downloading")
            )
            zip_path = os.path.join(ICONS_DIR, "icons_pack.zip")
            ensure_dir(ICONS_DIR)
            ok = download_file(ICONS_PACK_ZIP, zip_path)
            if ok:
                import zipfile

                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(ICONS_DIR)
                os.remove(zip_path)
                if hasattr(self, "parent_ui") and hasattr(self.parent_ui, "apply_i18n"):
                    self.parent_ui.apply_i18n()
                QMessageBox.information(
                    self, self._t("download_done"), self._t("download_done")
                )
            else:
                QMessageBox.warning(
                    self, self._t("download_fail"), self._t("download_fail")
                )
        except Exception as e:
            QMessageBox.critical(
                self, self._t("download_fail"), f"{self._t('download_fail')}\n{e}"
            )

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.startPos = e.globalPos()

    def mouseMoveEvent(self, e):
        if self.startPos:
            delta = e.globalPos() - self.startPos
            self.move(self.pos() + delta)
            self.startPos = e.globalPos()

    def mouseReleaseEvent(self, e):
        self.startPos = None


class DownloadWorker(QThread):
    """Worker thread to download audio using yt_dlp with progress reporting and cancellation."""

    success = pyqtSignal(str, str, object, object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._is_cancelled = False

    def cancel(self):
        """Signal to request cancellation from the GUI thread."""
        self._is_cancelled = True
        self.status.emit("cancel_requested")

    def run(self):
        try:

            def progress_hook(d):
                # d is a dict provided by yt_dlp; handle downloading and finished statuses
                try:
                    if d.get("status") == "downloading":
                        downloaded = d.get("downloaded_bytes") or d.get(
                            "downloaded_bytes", 0
                        )
                        total = (
                            d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        )
                        if total and downloaded is not None:
                            pct = int(downloaded * 100 / total) if total else 0
                            self.progress.emit(max(0, min(100, pct)))
                        self.status.emit("downloading")
                    elif d.get("status") == "finished":
                        self.progress.emit(100)
                        self.status.emit("finished")
                except Exception:
                    pass
                # cancellation check
                if self._is_cancelled:
                    raise Exception("Download cancelled")

            file_path, title, timeline, cover = audio_download(
                self.url,
                progress_hook=progress_hook,
                cancel_check=lambda: self._is_cancelled,
            )
            if self._is_cancelled:
                # emit error to indicate cancellation
                self.error.emit("Cancelled")
                return
            self.success.emit(file_path, title, timeline, cover)
        except Exception as e:
            self.error.emit(str(e))


class DownloadProgressDialog(QDialog):
    """Simple dialog that shows download progress and allows cancelling."""

    def __init__(self, parent=None, title=None, label=None):
        super().__init__(parent)
        self.setWindowTitle(title or "Downloading")
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.layout = QVBoxLayout(self)
        self.label = QLabel(label or "Downloading...")
        self.layout.addWidget(self.label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.layout.addWidget(self.progress)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.layout.addWidget(self.cancel_btn)
        self.cancelled = False

    def set_progress(self, v: int):
        self.progress.setValue(int(v))

    def set_status(self, s: str):
        if s == "downloading":
            self.label.setText("Downloading...")
        elif s == "finished":
            self.label.setText("Finishing...")
            # disable cancel at finish
            try:
                self.cancel_btn.setEnabled(False)
            except Exception:
                pass
        elif s == "cancel_requested":
            self.label.setText("Cancelling...")

    def _on_cancel(self):
        self.cancelled = True
        self.cancel_btn.setEnabled(False)
        self.label.setText("Cancelling...")


class DownloadHistoryDialog(QDialog):
    """Dialog that shows recent download history entries."""

    def __init__(self, parent=None, history=None):
        super().__init__(parent)
        self.setWindowTitle("Download History")
        self.layout = QVBoxLayout(self)
        self.list_w = QListWidget()
        self.layout.addWidget(self.list_w)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        self.layout.addWidget(close_btn)
        self.history = history or []
        self.reload()

    def reload(self):
        self.list_w.clear()
        for entry in reversed(self.history[-50:]):  # show up to last 50 entries
            txt = f"[{entry.get('status','?')}] {entry.get('title') or entry.get('url') or ''} "
            if entry.get("message"):
                txt += f"- {entry.get('message')}"
            self.list_w.addItem(txt)


class MusicPlayerUI(QWidget):
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

    def download_from_youtube(self):
        url = self.topbar.url_input.text().strip()
        if not url:
            return

        if hasattr(self, "download_thread") and self.download_thread.isRunning():
            return

        # record last url for retry purposes
        self.last_download_url = url

        # record initial history entry
        try:
            self.download_history.append(
                {"url": url, "title": None, "status": "started", "message": None}
            )
        except Exception:
            pass

        # show a non-modal progress dialog with cancel
        self.download_progress = DownloadProgressDialog(
            self,
            title=self._t("msg_downloading_title"),
            label=self._t("msg_downloading_text"),
        )

        self.download_thread = DownloadWorker(url)
        # connect progress/status signals
        self.download_thread.progress.connect(
            lambda v: self.download_progress.set_progress(v)
        )
        self.download_thread.status.connect(
            lambda s: self.download_progress.set_status(s)
        )
        # wire cancel button to request cancellation
        self.download_progress.cancel_btn.clicked.connect(self.download_thread.cancel)

        self.download_thread.success.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)

        # close dialog when finished or error
        self.download_thread.finished.connect(lambda: (self.download_progress.close()))

        self.download_progress.show()
        self.download_thread.start()

    def _on_download_finished(self, file_path, title, timeline, cover):
        self._force_close_download_msg()  # 🔴 ВАЖЛИВО

        # update history
        try:
            self.download_history.append(
                {
                    "url": getattr(self, "last_download_url", None),
                    "title": title,
                    "status": "success",
                    "message": None,
                }
            )
        except Exception:
            pass

        self.topbar.url_input.clear()
        self._scan_songs_dir()

        # update history dialog if open
        try:
            if (
                hasattr(self, "download_history_dialog")
                and self.download_history_dialog
            ):
                self.download_history_dialog.reload()
        except Exception:
            pass

        QMessageBox.information(
            self, self._t("download_done"), self._t("download_done")
        )

    def _on_download_error(self, error_text):
        self._force_close_download_msg()  # 🔴 ВАЖЛИВО

        # record history
        try:
            self.download_history.append(
                {
                    "url": getattr(self, "last_download_url", None),
                    "title": None,
                    "status": (
                        "error"
                        if error_text and "cancel" not in (error_text or "").lower()
                        else "cancelled"
                    ),
                    "message": str(error_text),
                }
            )
            if (
                hasattr(self, "download_history_dialog")
                and self.download_history_dialog
            ):
                self.download_history_dialog.reload()
        except Exception:
            pass

        if error_text and "cancel" in (error_text or "").lower():
            QMessageBox.information(
                self, self._t("msg_downloading_title"), "Download cancelled"
            )
            return

        # present a retry dialog
        try:
            res = QMessageBox.question(
                self,
                self._t("msg_error_title"),
                self._t("msg_error_download_hint") + "\n\nRetry?",
                QMessageBox.Retry | QMessageBox.Cancel,
            )
            if res == QMessageBox.Retry:
                # attempt retry using the last recorded URL
                if getattr(self, "last_download_url", None):
                    self.topbar.url_input.setText(self.last_download_url)
                    QTimer.singleShot(250, lambda: self.download_from_youtube())
                return
        except Exception:
            logger.exception("Error showing retry dialog")

        QMessageBox.critical(
            self, self._t("msg_error_title"), self._t("msg_error_download_hint")
        )

    def _force_close_download_msg(self):
        logger.debug("HIDE DOWNLOAD MSG")
        if hasattr(self, "download_msg") and self.download_msg:
            try:
                self.download_msg.hide()
                self.download_msg.deleteLater()
            except Exception:
                pass
        if hasattr(self, "download_progress") and self.download_progress:
            try:
                self.download_progress.close()
                self.download_progress.deleteLater()
            except Exception:
                pass

    def show_download_history(self):
        try:
            if (
                not hasattr(self, "download_history_dialog")
                or not self.download_history_dialog
            ):
                self.download_history_dialog = DownloadHistoryDialog(
                    self, self.download_history
                )
            else:
                self.download_history_dialog.reload()
            self.download_history_dialog.show()
            self.download_history_dialog.raise_()
            self.download_history_dialog.activateWindow()
        except Exception as e:
            logger.exception("Error showing download history: %s", e)
            QMessageBox.critical(self, self._t("msg_error_title"), str(e))
            self.download_msg = None

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
    # Playback logic
    # ---------------------------
    def _connect_and_play_path(self, path):
        # low-level: point player to file and play
        url = QUrl.fromLocalFile(os.path.normpath(path))
        self.player.setMedia(QMediaContent(url))
        self.player.play()
        self.play_btn.setText("⏸")

    def play_song(self, index):
        """Play by index in current_playlist (and snapshot playback playlist)"""
        if not (0 <= index < len(self.current_playlist)):
            return
        # snapshot playback playlist when playback starts
        self.playback_playlist = list(self.current_playlist)
        self.playback_playlist_name = self.current_playlist_name
        self.current_index = index
        p = self.playback_playlist[index]
        self._connect_and_play_path(p)
        # --- Discord Rich Presence update ---
        try:
            if self.rpc:
                song_title = os.path.splitext(os.path.basename(p))[0]
                start_time = int(time.time())
                self.rpc.update(
                    details=f"🎵 {song_title}",
                    state="Listening in PyFy",
                    start=start_time,
                    large_text="PyFy Music Player",
                )

                # Запускаем поток обновления времени
                self.rpc_running = True
                if self.rpc_thread and self.rpc_thread.is_alive():
                    self.rpc_running = False
                    time.sleep(0.2)
                self.rpc_thread = threading.Thread(
                    target=self._update_rpc_time, args=(song_title,)
                )
                self.rpc_thread.daemon = True
                self.rpc_thread.start()
        except Exception as e:
            logger.exception("[Discord RPC Update Error] %s", e)
        # save history
        if p not in self.listening_history:
            self.listening_history.append(p)
            self.save_history()

        # refresh hearts
        self.refresh_current_view()

        # --- Обновляем большую обложку ---
        song_path = self.current_playlist[self.current_index]
        cover_name = os.path.splitext(os.path.basename(song_path))[0] + ".webp"
        cover_path = os.path.join(COVERS_DIR, cover_name)

        if self.show_covers_enabled and os.path.exists(cover_path):
            pixmap = QPixmap(cover_path)
            if pixmap.isNull():
                self.cover_label.clear()
                self.cover_label.setText("🎵")
            else:
                # Размер и сглаживание
                size = self.cover_label.size()
                pixmap = pixmap.scaled(
                    size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )

                # Создаём новое изображение с прозрачным фоном
                rounded = QPixmap(size)
                rounded.fill(Qt.transparent)

                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                radius = 12
                path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                # self._connect_and_play_path(p)
                self.cover_label.setPixmap(rounded)
                self.cover_label.setText("")
        else:
            self.cover_label.clear()
            self.cover_label.setText("🎵")

    def _toggle_play(self):
        st = self.player.state()
        if st == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶")
        elif st == QMediaPlayer.PausedState:
            self.player.play()
            self.play_btn.setText("⏸")
        else:
            if self.current_index == -1 and self.current_playlist:
                self.play_song(0)

    def _play_next(self):
        """Наступний трек з підтримкою повтору"""
        if not self.current_playlist:
            return

        # Якщо repeat_mode == "one", просто перезапускаємо поточний трек
        if hasattr(self, "repeat_mode") and self.repeat_mode == "one":
            self.player.setPosition(0)
            if self.player.state() != QMediaPlayer.PlayingState:
                self.player.play()
            return

        # Інакше йдемо до наступного треку
        self.current_index = (self.current_index + 1) % len(self.current_playlist)
        self.play_song(self.current_index)

    def _play_prev(self):
        pl = self.playback_playlist or self.current_playlist
        if self.current_index > 0:
            self.play_song(self.current_index - 1)
        elif self.repeat_mode == 1 and len(pl) > 0:
            self.play_song(len(pl) - 1)

    def _toggle_repeat(self):
        # cycle 0 -> 1 -> 2 -> 0
        self.repeat_mode = (self.repeat_mode + 1) % 3
        if self.repeat_mode == 0:
            self.repeat_btn.setText("🔁")
            self.repeat_btn.setStyleSheet(AnimatedButton("", "icon").styleSheet())
        elif self.repeat_mode == 1:
            self.repeat_btn.setText("🔁")
            self.repeat_btn.setStyleSheet(
                "background: #4a9eff; border-radius: 8px; color: white;"
            )
        else:
            self.repeat_btn.setText("🔁1")
            self.repeat_btn.setStyleSheet(
                "background: #4a9eff; border-radius: 8px; color: white;"
            )

    def _update_rpc_time(self, song_title):
        """Комбінує elapsed time (автоматичний) + progress bar (текстовий)"""
        last_update_time = 0
        update_interval = 10  # оновлення прогрес-бару кожні 10 сек

        while self.rpc_running:
            try:
                current_time = time.time()

                if current_time - last_update_time >= update_interval:
                    pos = self.player.position() // 1000
                    dur = self.player.duration() // 1000

                    # Прогрес бар оновлюємо рідко
                    progress = self._get_progress_bar(pos, dur)
                    tot = (
                        time.strftime("%M:%S", time.gmtime(dur)) if dur > 0 else "00:00"
                    )

                    # start - для автоматичного тикання elapsed time
                    start_time = int(time.time()) - pos

                    self.rpc.update(
                        details=f"🎵 {song_title}",
                        state=f"{progress} {tot}",  # прогрес + загальний час
                        start=start_time,  # elapsed тікає автоматично внизу
                        large_image="pyfy",
                        large_text="PyFy Music Player",
                    )

                    last_update_time = current_time

            except Exception as e:
                logger.exception("[RPC Update Error] %s", e)

            time.sleep(2)  # перевірка кожні 2 секунди

    def _get_progress_bar(self, position, duration, length=12):
        """Візуальний прогрес бар"""
        if duration <= 0:
            return "▱" * length

        filled = int((position / duration) * length)
        bar = "▰" * filled + "▱" * (length - filled)
        return bar

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


# ---------------------------
# Entry point
# ---------------------------
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
