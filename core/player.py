from PyQt5.QtGui import QPixmap, QPainterPath, QPainter
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl
import os
import time
import threading
from utils.logger import logger
from config.constants import COVERS_DIR
from ui.widgets import AnimatedButton


def _connect_and_play_path(self, path):
    # low-level: point player to file and play
    url = QUrl.fromLocalFile(os.path.normpath(path))
    self.player.setMedia(QMediaContent(url))
    self.player.play()
    self.play_btn.setText("⏸")


def play_song(self, index):
    if not (0 <= index < len(self.current_playlist)):
        return
    # snapshot playback playlist when playback starts
    self.playback_playlist = list(self.current_playlist)
    self.playback_playlist_name = self.current_playlist_name
    self.current_index = index
    p = self.playback_playlist[index]
    self._connect_and_play_path(p)
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
                tot = time.strftime("%M:%S", time.gmtime(dur)) if dur > 0 else "00:00"

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
    if duration <= 0:
        return "▱" * length
    filled = int((position / duration) * length)
    bar = "▰" * filled + "▱" * (length - filled)
    return bar
