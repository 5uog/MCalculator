# FILE: ui/assets/texture_store.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtGui import QPixmap

from ui.assets.image_utils import load_png_pixmap
from utils.paths import asset_path, normalize_saved_path, resolve_saved_path

SKIN_A_KEY = "skin_a"
SKIN_B_KEY = "skin_b"
BLOCK_KEY = "block_andesite"

@dataclass
class TextureStore:
    """
    Centralized texture registry.
    - Renderer resolves textures by string key.
    - Paths are stored separately for persistence.
    """
    _pix: Dict[str, QPixmap]
    _path_by_key: Dict[str, str]

    def __init__(self) -> None:
        self._pix = {}
        self._path_by_key = {}

    def get(self, key: str) -> Optional[QPixmap]:
        return self._pix.get(str(key))

    def path_for(self, key: str) -> str:
        return str(self._path_by_key.get(str(key), ""))

    def set_from_path(self, key: str, p: Path | None) -> bool:
        if p is None:
            self._pix.pop(str(key), None)
            self._path_by_key[str(key)] = ""
            return False

        pm = load_png_pixmap(p)
        ok = pm is not None
        if ok:
            self._pix[str(key)] = pm  # type: ignore[assignment]
            self._path_by_key[str(key)] = normalize_saved_path(p)
        else:
            self._pix.pop(str(key), None)
            self._path_by_key[str(key)] = normalize_saved_path(p)
        return ok

    def set_from_saved_string(self, key: str, saved: str) -> bool:
        p = resolve_saved_path(saved)
        return self.set_from_path(key, p)

    def load_default_block(self) -> bool:
        return self.set_from_path(BLOCK_KEY, asset_path("blocks", "andesite.png"))

    def load_default_skin_for(self, key: str, model_name: str) -> bool:
        name = str(model_name).strip().lower()
        fname = "alex.png" if name == "alex" else "steve.png"
        return self.set_from_path(key, asset_path("skins", fname))