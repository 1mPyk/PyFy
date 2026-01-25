import urllib.request
from config.constants import VERSION_URL
from utils.logger import logger

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