# FILE: utils/config_locator.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from utils.config_store import load_json, save_json_atomic
from utils.paths import user_config_dir, config_file_path

_LOCATOR_FILENAME = "config_location.json"

def locator_path() -> Path:
    """Return the stable locator file path under the user config dir."""
    return user_config_dir() / _LOCATOR_FILENAME

def get_active_config_path() -> Path:
    """
    Resolve the active config.json path.
    If locator is missing or invalid, fall back to the default config path.
    """
    p = locator_path()
    raw = load_json(p)
    if isinstance(raw, dict):
        s = str(raw.get("config_path", "")).strip()
        if s:
            try:
                return Path(s).expanduser().resolve()
            except Exception:
                return Path(s)
    return config_file_path()

def set_active_config_path(path: Path) -> None:
    """Persist the chosen config.json path into the locator."""
    try:
        p = Path(path).expanduser().resolve()
    except Exception:
        p = Path(str(path))
    save_json_atomic(locator_path(), {"config_path": str(p)})