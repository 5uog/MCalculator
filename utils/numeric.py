# FILE: utils/numeric.py
from __future__ import annotations

import math
from typing import Any

def clampf(v: float, lo: float, hi: float) -> float:
    """Clamp a float into [lo, hi]."""
    return lo if v < lo else hi if v > hi else v

def clamp01(v: float) -> float:
    """Clamp a float into [0, 1]."""
    return clampf(float(v), 0.0, 1.0)

def finite_or(v: Any, default: float) -> float:
    """Convert to float and return default if conversion fails or non-finite."""
    try:
        x = float(v)
    except Exception:
        return float(default)
    if not math.isfinite(x):
        return float(default)
    return float(x)

def clampf_finite(v: Any, lo: float, hi: float, default: float) -> float:
    """finite_or(v, default) then clamp into [lo, hi]."""
    x = finite_or(v, default)
    return clampf(x, float(lo), float(hi))

def clampi(v: Any, lo: int, hi: int, default: int) -> int:
    """Convert to int and clamp into [lo, hi], falling back to default on failure."""
    try:
        x = int(v)
    except Exception:
        return int(default)
    if x < int(lo):
        return int(lo)
    if x > int(hi):
        return int(hi)
    return int(x)