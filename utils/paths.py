# FILE: utils/paths.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

APP_NAME = "MCalculator"

def resource_root() -> Path:
    """
    Return the root directory for bundled resources.
    - PyInstaller (onefile/onedir): sys._MEIPASS
    - Dev run: walk up from this file until 'assets' is found
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve()

    here = Path(__file__).resolve()
    for p in [here.parent, *here.parents]:
        if (p / "assets").is_dir():
            return p
    # Fallback: utils/paths.py -> utils -> project root (best effort)
    return here.parents[1]

def asset_path(*parts: str) -> Path:
    """Return absolute path to an asset under the assets/ directory."""
    return resource_root() / "assets" / Path(*parts)

def _windows_appdata_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata)
    return Path.home() / "AppData" / "Roaming"

def _mac_app_support_dir() -> Path:
    return Path.home() / "Library" / "Application Support"

def _linux_config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"

def user_config_dir(app_name: str = APP_NAME) -> Path:
    """
    Per-user config directory (outside install dir).
    This is the correct place for persisted settings for exe builds.
    """
    plat = sys.platform.lower()
    if plat.startswith("win"):
        base = _windows_appdata_dir()
    elif plat == "darwin":
        base = _mac_app_support_dir()
    else:
        base = _linux_config_dir()
    return (base / app_name).resolve()

def config_file_path(app_name: str = APP_NAME, filename: str = "config.json") -> Path:
    return user_config_dir(app_name) / filename

def normalize_saved_path(p: Optional[Path]) -> str:
    """
    Persist paths in a portable way.
    - If path points inside assets/, store as '@asset/<relative>'
    - Else store absolute string
    """
    if p is None:
        return ""
    try:
        pp = p.resolve()
    except Exception:
        pp = Path(str(p))

    root = asset_path().resolve()
    try:
        rel = pp.relative_to(root)
        return "@asset/" + rel.as_posix()
    except Exception:
        return str(pp)

def resolve_saved_path(s: str) -> Optional[Path]:
    """
    Resolve a persisted path string.
    - '@asset/<relative>' -> asset_path(<relative>)
    - else -> Path(s) if non-empty
    """
    ss = str(s or "").strip()
    if not ss:
        return None
    if ss.startswith("@asset/"):
        rel = ss[len("@asset/") :]
        return asset_path(*Path(rel).parts)
    return Path(ss)