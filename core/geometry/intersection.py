# FILE: core/geometry/intersection.py
from __future__ import annotations
from dataclasses import dataclass
import math
from core.geometry.vec3 import Vec3
from core.geometry.aabb import AABB

@dataclass(frozen=True)
class SegmentHit:
    hit: bool
    t_enter: float
    t_exit: float

def segment_intersects_aabb(p0: Vec3, p1: Vec3, box: AABB, eps: float = 1e-12, start_nudge: float = 1e-9) -> SegmentHit:
    """
    Slab method for segment [p0, p1].

    Notes:
        - A small start-point nudge along the segment direction reduces boundary flicker
          when the start lies exactly on an AABB face/edge due to floating-point ties.
        - eps is used both for "parallel" detection and as a loose boundary tolerance.
    """
    d = p1 - p0
    dlen = d.norm()
    if dlen > 1e-15 and start_nudge > 0.0:
        p0 = p0 + d * (float(start_nudge) / float(dlen))
        d = p1 - p0

    tmin, tmax = 0.0, 1.0

    for axis in ("x", "y", "z"):
        p0a = getattr(p0, axis)
        da = getattr(d, axis)
        mina = getattr(box.mn, axis)
        maxa = getattr(box.mx, axis)

        if abs(da) < eps:
            if p0a < (mina - start_nudge) or p0a > (maxa + start_nudge):
                return SegmentHit(False, 0.0, 0.0)
        else:
            inv = 1.0 / da
            t1 = (mina - p0a) * inv
            t2 = (maxa - p0a) * inv
            if t1 > t2:
                t1, t2 = t2, t1
            tmin = max(tmin, t1)
            tmax = min(tmax, t2)
            if tmin > tmax + eps:
                return SegmentHit(False, 0.0, 0.0)

    if tmax < 0.0 or tmin > 1.0:
        return SegmentHit(False, 0.0, 0.0)

    return SegmentHit(True, max(0.0, float(tmin)), min(1.0, float(tmax)))