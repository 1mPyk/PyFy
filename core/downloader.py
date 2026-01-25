import yt_dlp as youtube_dl
import os
import shutil
from utils.sanitize import sanitize_filename, remove_files_if_exist
from utils.logger import logger
from utils.files import ensure_dir
from config.constants import (
    SONGS_DIR,
    COVERS_DIR
)

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