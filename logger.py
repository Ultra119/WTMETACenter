import os
import sys
from datetime import datetime

LOG_PATH = "debug_log.txt"
MAX_BYTES = 2 * 1024 * 1024
_LEVELS = ("DEBUG", "INFO", "WARN", "ERROR")

_STDOUT_FROM = "WARN"


def _to_stdout(level: str) -> bool:
    return _LEVELS.index(level) >= _LEVELS.index(_STDOUT_FROM)


def _rotate() -> None:
    try:
        if os.path.getsize(LOG_PATH) < MAX_BYTES:
            return
    except OSError:
        return

    try:
        backup = LOG_PATH + ".1"
        if os.path.exists(backup):
            os.remove(backup)
        os.replace(LOG_PATH, backup)
    except OSError:
        pass


def log(message, level: str = "DEBUG") -> None:
    level = level.upper()
    if level not in _LEVELS:
        level = "DEBUG"

    text = str(message)

    if _to_stdout(level):
        print(f"[{level}] {text}", file=sys.stderr)

    try:
        _rotate()
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{stamp} [{level}] {text}\n")
    except OSError as e:
        print(f"[WARN] cannot write {LOG_PATH}: {e}", file=sys.stderr)


def log_debug(message) -> None:
    log(message, "DEBUG")


def log_info(message) -> None:
    log(message, "INFO")


def log_warn(message) -> None:
    log(message, "WARN")


def log_error(message) -> None:
    log(message, "ERROR")
