import yt_dlp as youtube_dl
import os
import shutil
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from utils.sanitize import sanitize_filename, remove_files_if_exist
from utils.logger import logger
from utils.files import ensure_dir
from ui.dialogs import DownloadHistoryDialog, DownloadProgressDialog
from config.constants import (
    SONGS_DIR,
    COVERS_DIR
)

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
            remove_files_if_exist(tmp_files)
        except Exception:
            logger.exception("Error cleaning up partial files")
        raise
    
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
    self._force_close_download_msg()

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
    self._force_close_download_msg()

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