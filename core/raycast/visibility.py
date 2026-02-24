# FILE: core/raycast/visibility.py
from __future__ import annotations
from core.geometry.vec3 import Vec3
from core.geometry.aabb import AABB
from core.geometry.intersection import segment_intersects_aabb
from core.raycast.voxel_dda import segment_hits_solid_blocks_dda

def is_visible(
    attacker: Vec3,
    target_point: Vec3,
    blockers: list[AABB] | None = None,
    solid_blocks: set[tuple[int, int, int]] | None = None,
    ignore: AABB | None = None
) -> bool:
    """
    Visibility predicate.
    - If solid_blocks is provided, use fast grid traversal for unit blocks.
    - Otherwise, use generic AABB slab intersection against blockers.
    """
    if solid_blocks is not None:
        return not segment_hits_solid_blocks_dda(attacker, target_point, solid_blocks)

    if blockers is None:
        return True

    for b in blockers:
        if ignore is not None and b == ignore:
            continue
        h = segment_intersects_aabb(attacker, target_point, b)
        if h.hit:
            return False
    return True