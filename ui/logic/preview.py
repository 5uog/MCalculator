# FILE: ui/logic/preview.py
from __future__ import annotations
from core.reach.attack import AttackEval, evaluate_attack
from scene.world import World

def compute_attack_previews(world: World, reach: float, surface_samples: int, attack_samples: int, attack_offset: float = 0.8) -> tuple[AttackEval, AttackEval]:
    """
    Compute preview evaluations (A->B and B->A) for the current world state.
    """
    solids = world.solid_block_keys()

    a_eye = world.player_a.eye_point()
    b_eye = world.player_b.eye_point()

    a_box = world.player_a.aabb()
    b_box = world.player_b.aabb()

    ev_a = evaluate_attack(
        attacker_eye=a_eye,
        target=b_box,
        solid_blocks=solids,
        reach=float(reach),
        surface_samples=int(surface_samples),
        attack_offset=float(attack_offset),
        attack_samples=int(attack_samples),
    )
    ev_b = evaluate_attack(
        attacker_eye=b_eye,
        target=a_box,
        solid_blocks=solids,
        reach=float(reach),
        surface_samples=int(surface_samples),
        attack_offset=float(attack_offset),
        attack_samples=int(attack_samples),
    )
    return ev_a, ev_b