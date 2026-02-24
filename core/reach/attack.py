# FILE: core/reach/attack.py
from __future__ import annotations
import math
from dataclasses import dataclass
from core.geometry.vec3 import Vec3
from core.geometry.aabb import AABB
from core.raycast.visibility import is_visible
from core.geometry.sampling import sample_aabb_surface, sample_segment

@dataclass(frozen=True)
class AttackEval:
    min_dist: float
    aim_target: Vec3
    any_visible: bool
    any_reachable: bool
    visible_frac: float
    within_reach_of_visible: float
    within_reach_of_total: float
    seg_start: Vec3
    seg_end: Vec3

def evaluate_attack(
    attacker_eye: Vec3,
    target: AABB,
    solid_blocks: set[tuple[int, int, int]] | None,
    reach: float,
    surface_samples: int,
    attack_offset: float = 0.8,
    attack_samples: int = 9
) -> AttackEval:
    """
    Evaluate attack feasibility with:
        - attacker point allowed to vary on a short segment from the eye toward the target
        - target represented by surface samples
    Occlusion metrics are computed by sample-point visibility.
    """
    closest = target.closest_point(attacker_eye)
    dvec = closest - attacker_eye
    dnorm = dvec.norm()
    if dnorm == 0.0:
        dirn = Vec3(0.0, 0.0, 0.0)
    else:
        dirn = dvec * (1.0 / dnorm)

    seg_start = attacker_eye
    seg_end = attacker_eye + dirn * float(attack_offset)

    att_pts = sample_segment(seg_start, seg_end, int(attack_samples))
    tgt_pts = sample_aabb_surface(target, int(surface_samples))

    total = len(tgt_pts)
    if total == 0:
        return AttackEval(
            min_dist=math.inf,
            aim_target=closest,
            any_visible=False,
            any_reachable=False,
            visible_frac=0.0,
            within_reach_of_visible=0.0,
            within_reach_of_total=0.0,
            seg_start=seg_start,
            seg_end=seg_end,
        )

    reach2 = float(reach) * float(reach)

    visible = 0
    reachable_visible = 0

    best2 = float("inf")
    best_p: Vec3 | None = None

    for p in tgt_pts:
        best_for_p2 = float("inf")
        visible_p = False

        for a in att_pts:
            if not is_visible(a, p, solid_blocks=solid_blocks):
                continue
            visible_p = True
            dx = a.x - p.x
            dy = a.y - p.y
            dz = a.z - p.z
            dist2 = dx*dx + dy*dy + dz*dz
            if dist2 < best_for_p2:
                best_for_p2 = dist2
                if best_for_p2 == 0.0:
                    break

        if visible_p:
            visible += 1
            if best_for_p2 <= reach2:
                reachable_visible += 1
            if best_for_p2 < best2:
                best2 = best_for_p2
                best_p = p

    any_visible = (visible > 0)
    any_reachable = (reachable_visible > 0)

    visible_frac = float(visible) / float(total)
    within_total = float(reachable_visible) / float(total)
    within_visible = (float(reachable_visible) / float(visible)) if visible > 0 else 0.0

    aim = best_p if best_p is not None else closest
    min_dist = math.sqrt(best2) if math.isfinite(best2) else math.inf

    return AttackEval(
        min_dist=float(min_dist),
        aim_target=aim,
        any_visible=any_visible,
        any_reachable=any_reachable,
        visible_frac=visible_frac,
        within_reach_of_visible=within_visible,
        within_reach_of_total=within_total,
        seg_start=seg_start,
        seg_end=seg_end,
    )