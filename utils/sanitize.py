import re
import os
import logging
from typing import Iterable, List

logger = logging.getLogger("PyFy")


def compare_versions(v1: str, v2: str) -> int:
    """Compare two semantic version strings.

    Returns:
        -1 if v1 < v2
         0 if equal
         1 if v1 > v2
    """
    try:
        a = [int(x) for x in v1.split(".")]
        b = [int(x) for x in v2.split(".")]
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
        # In case of malformed version, consider equal
        return 0


def sanitize_filename(name: str) -> str:
    """Remove characters not allowed in filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name)


def remove_files_if_exist(paths: Iterable[str]) -> List[str]:
    """Remove files if they exist and return the list of removed paths."""
    removed = []
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
                removed.append(p)
                logger.debug("Removed partial file: %s", p)
        except Exception:
            logger.exception("Failed to remove file: %s", p)
    return removed