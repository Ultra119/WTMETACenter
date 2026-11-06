import json
import math
import os

from logger import log_debug
from analytics.constants import DEFAULT_SETTINGS


def _is_valid(key: str, value) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False

    number = float(value)

    if not math.isfinite(number) or number < 0.0:
        return False
    if key in ("sigmoid_scale", "z_clip"):
        return number > 0.0
    return True


def _merge(loaded: dict) -> dict:
    merged = dict(DEFAULT_SETTINGS)

    for key, value in loaded.items():
        if key not in DEFAULT_SETTINGS:
            log_debug(f"settings.json: ignoring unknown key '{key}'")
            continue
        if not _is_valid(key, value):
            log_debug(f"settings.json: '{key}' = {value!r} rejected, keeping default")
            continue
        merged[key] = float(value)

    return merged


def load_settings(script_dir: str) -> dict:
    settings_path = os.path.join(script_dir, "settings.json")

    if not os.path.exists(settings_path):
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=4)
            log_debug("settings.json has been created with default values.")
        except Exception as e:
            log_debug(f"Failed to create settings.json: {e}")
        return dict(DEFAULT_SETTINGS)

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        if not isinstance(loaded, dict):
            log_debug("settings.json is not an object; defaults are being used.")
            return dict(DEFAULT_SETTINGS)

        merged = _merge(loaded)
        log_debug(f"settings.json downloaded: {merged}")
        return merged

    except Exception as e:
        log_debug(f"Error reading settings.json; defaults are being used: {e}")
        return dict(DEFAULT_SETTINGS)
