import urllib.request
import os
from versioncheck import logger

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