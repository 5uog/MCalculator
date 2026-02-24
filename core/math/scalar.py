# FILE: core/math/scalar.py
from __future__ import annotations

def clamp(v: float, lo: float, hi: float) -> float:
    """Clamp v into [lo, hi]."""
    return lo if v < lo else hi if v > hi else v