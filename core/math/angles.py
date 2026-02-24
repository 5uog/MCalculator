# FILE: core/math/angles.py
from __future__ import annotations
import math
from core.math.scalar import clamp

def wrap_pi(a: float) -> float:
    """Wrap angle to (-pi, pi]."""
    return (a + math.pi) % (2.0 * math.pi) - math.pi

def clamp_pitch(pitch_rad: float, lim_deg: float = 89.9) -> float:
    """Clamp pitch to [-lim, +lim] degrees."""
    lim = math.radians(float(lim_deg))
    return clamp(float(pitch_rad), -lim, lim)