# FILE: render/viz/items.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
from core.geometry.aabb import AABB

ColorRGB = tuple[int, int, int]

@dataclass
class RenderItem:
    """
    Qt-agnostic render item for the viewport.
    Texture lookup is done via texture_key in the UI renderer.
    """
    kind: Literal["aabb", "segment", "cross", "tex_quad"]
    color: ColorRGB = (255, 255, 255)
    label: str = ""

    opacity: float = 1.0

    aabb: Optional[AABB] = None
    a: Optional[np.ndarray] = None
    b: Optional[np.ndarray] = None

    p: Optional[np.ndarray] = None
    size_px: int = 10

    verts: Optional[np.ndarray] = None  # (4,3) world-space
    texture_key: Optional[str] = None
    src_rect: Optional[tuple[float, float, float, float]] = None  # (x,y,w,h) in pixels, None => full texture
    normal: Optional[np.ndarray] = None  # (3,) world normal