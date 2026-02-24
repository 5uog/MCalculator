# FILE: core/geometry/sampling.py
from __future__ import annotations
from functools import lru_cache
from core.geometry.vec3 import Vec3
from core.geometry.aabb import AABB

def _linspace_01(n: int) -> list[float]:
    n = int(n)
    if n <= 1:
        return [0.5]
    inv = 1.0 / float(n - 1)
    return [float(i) * inv for i in range(n)]

@lru_cache(maxsize=256)
def _surface_offsets_cached(sx_q: int, sy_q: int, sz_q: int, n: int) -> tuple[Vec3, ...]:
    """
    Cache surface offsets for a box of size (sx, sy, sz).
    The sizes are quantized integers in microunits to keep the cache stable.

    Interpretation of n:
        n is the reference resolution for the longest dimension.
        Other dimensions get scaled sample counts to keep a roughly uniform surface density.
    """
    sx = float(sx_q) * 1e-6
    sy = float(sy_q) * 1e-6
    sz = float(sz_q) * 1e-6

    n = max(1, int(n))
    max_dim = max(abs(sx), abs(sy), abs(sz), 1e-12)

    def _count_for(dim: float) -> int:
        if n <= 1:
            return 1
        if abs(dim) <= 1e-12:
            return 1
        # Scale samples so that density is roughly constant across faces.
        scaled = 1.0 + (float(n - 1) * (abs(dim) / max_dim))
        return max(2, int(round(scaled)))

    nx = _count_for(sx)
    ny = _count_for(sy)
    nz = _count_for(sz)

    xs = [sx * t for t in _linspace_01(nx)]
    ys = [sy * t for t in _linspace_01(ny)]
    zs = [sz * t for t in _linspace_01(nz)]

    # Deduplicate edge/corner points using microunit quantization.
    uniq: dict[tuple[int, int, int], Vec3] = {}

    def _add(x: float, y: float, z: float) -> None:
        k = (int(round(x * 1e6)), int(round(y * 1e6)), int(round(z * 1e6)))
        if k not in uniq:
            uniq[k] = Vec3(float(x), float(y), float(z))

    for y in ys:
        for z in zs:
            _add(0.0, y, z)
            _add(sx, y, z)

    for x in xs:
        for z in zs:
            _add(x, 0.0, z)
            _add(x, sy, z)

    for x in xs:
        for y in ys:
            _add(x, y, 0.0)
            _add(x, y, sz)

    return tuple(uniq.values())

def sample_aabb_surface(box: AABB, n: int) -> list[Vec3]:
    """
    Surface samples on the AABB.

    n is a reference resolution for the longest dimension (see cache docstring).
    """
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