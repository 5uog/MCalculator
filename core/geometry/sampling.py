# FILE: core/geometry/sampling.py
from __future__ import annotations
from functools import lru_cache
from core.geometry.vec3 import Vec3
from core.geometry.aabb import AABB

@lru_cache(maxsize=128)
def _surface_offsets_cached(sx_q: int, sy_q: int, sz_q: int, n: int) -> tuple[Vec3, ...]:
    """
    Cache surface offsets for a box of size (sx, sy, sz).
    The sizes are quantized integers in microunits to keep the cache stable.
    """
    sx = float(sx_q) * 1e-6
    sy = float(sy_q) * 1e-6
    sz = float(sz_q) * 1e-6

    n = max(1, int(n))
    xs = [sx * (i / (n - 1) if n > 1 else 0.5) for i in range(n)]
    ys = [sy * (i / (n - 1) if n > 1 else 0.5) for i in range(n)]
    zs = [sz * (i / (n - 1) if n > 1 else 0.5) for i in range(n)]

    pts: list[Vec3] = []

    for y in ys:
        for z in zs:
            pts.append(Vec3(0.0, y, z))
            pts.append(Vec3(sx, y, z))

    for x in xs:
        for z in zs:
            pts.append(Vec3(x, 0.0, z))
            pts.append(Vec3(x, sy, z))

    for x in xs:
        for y in ys:
            pts.append(Vec3(x, y, 0.0))
            pts.append(Vec3(x, y, sz))

    return tuple(pts)

def sample_aabb_surface(box: AABB, n: int) -> list[Vec3]:
    """Uniform grid samples on the surface of an AABB."""
    n = max(1, int(n))
    mn, mx = box.mn, box.mx
    sx = float(mx.x - mn.x)
    sy = float(mx.y - mn.y)
    sz = float(mx.z - mn.z)

    sx_q = int(round(sx * 1e6))
    sy_q = int(round(sy * 1e6))
    sz_q = int(round(sz * 1e6))

    offs = _surface_offsets_cached(sx_q, sy_q, sz_q, n)
    return [Vec3(mn.x + o.x, mn.y + o.y, mn.z + o.z) for o in offs]

def sample_segment(p0: Vec3, p1: Vec3, n: int) -> list[Vec3]:
    """Uniform samples (including endpoints) on a segment."""
    n = max(1, int(n))
    if n == 1:
        return [p0]
    pts: list[Vec3] = []
    d = p1 - p0
    inv = 1.0 / float(n - 1)
    for i in range(n):
        t = float(i) * inv
        pts.append(p0 + d * t)
    return pts