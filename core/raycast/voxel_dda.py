# FILE: core/raycast/voxel_dda.py
from __future__ import annotations
import math
from core.geometry.vec3 import Vec3

def segment_hits_solid_blocks_dda(p0: Vec3, p1: Vec3, solids: set[tuple[int, int, int]]) -> bool:
    """
    Fast voxel traversal for unit blocks on an integer grid.
    The segment is tested against occupied grid cells using 3D DDA.
    """
    x0, y0, z0 = float(p0.x), float(p0.y), float(p0.z)
    x1, y1, z1 = float(p1.x), float(p1.y), float(p1.z)
    dx, dy, dz = (x1 - x0), (y1 - y0), (z1 - z0)

    eps = 1e-9
    if dx == 0.0 and dy == 0.0 and dz == 0.0:
        vx = math.floor(x0 + eps)
        vy = math.floor(y0 + eps)
        vz = math.floor(z0 + eps)
        return (vx, vy, vz) in solids

    # Slightly nudge the start point along the direction to avoid boundary ambiguity.
    inv_len = 1.0 / math.sqrt(dx*dx + dy*dy + dz*dz)
    x0 += dx * inv_len * eps
    y0 += dy * inv_len * eps
    z0 += dz * inv_len * eps

    vx = int(math.floor(x0))
    vy = int(math.floor(y0))
    vz = int(math.floor(z0))

    step_x = 1 if dx > 0.0 else (-1 if dx < 0.0 else 0)
    step_y = 1 if dy > 0.0 else (-1 if dy < 0.0 else 0)
    step_z = 1 if dz > 0.0 else (-1 if dz < 0.0 else 0)

    if step_x != 0:
        next_x = float(vx + 1) if step_x > 0 else float(vx)
        t_max_x = (next_x - x0) / dx
        t_delta_x = 1.0 / abs(dx)
    else:
        t_max_x = float("inf")
        t_delta_x = float("inf")

    if step_y != 0:
        next_y = float(vy + 1) if step_y > 0 else float(vy)
        t_max_y = (next_y - y0) / dy
        t_delta_y = 1.0 / abs(dy)
    else:
        t_max_y = float("inf")
        t_delta_y = float("inf")

    if step_z != 0:
        next_z = float(vz + 1) if step_z > 0 else float(vz)
        t_max_z = (next_z - z0) / dz
        t_delta_z = 1.0 / abs(dz)
    else:
        t_max_z = float("inf")
        t_delta_z = float("inf")

    t = 0.0
    while t <= 1.0:
        if (vx, vy, vz) in solids:
            return True

        if t_max_x < t_max_y:
            if t_max_x < t_max_z:
                vx += step_x
                t = t_max_x
                t_max_x += t_delta_x
            else:
                vz += step_z
                t = t_max_z
                t_max_z += t_delta_z
        else:
            if t_max_y < t_max_z:
                vy += step_y
                t = t_max_y
                t_max_y += t_delta_y
            else:
                vz += step_z
                t = t_max_z
                t_max_z += t_delta_z

    return False