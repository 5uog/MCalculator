# FILE: sim/runner.py
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Callable

from core.geometry.vec3 import Vec3
from core.reach.attack import evaluate_attack
from core.metrics.types import TrialResult, SummaryStats
from core.metrics.summary import summarize
from scene.world import World
from sim.jitter import JitterSpec
from sim.config import SimConfig

ProgressCb = Callable[[float, str, int, int], None]

def _one_direction(world: World, attacker_name: str, defender_name: str,
                   jitter: JitterSpec, cfg: SimConfig,
                   progress_cb: ProgressCb | None,
                   progress_base: float, progress_span: float,
                   stop_flag: Callable[[], bool] | None) -> list[TrialResult]:
    rng = jitter.rng()

    attacker = world.player_a if attacker_name == "A" else world.player_b
    defender = world.player_b if defender_name == "B" else world.player_a

    base_a = attacker.pos
    base_b = defender.pos

    solids = world.solid_block_keys()

    results: list[TrialResult] = []
    trials = int(cfg.trials)

    stride = max(1, trials // 200)

    for i in range(trials):
        if stop_flag is not None and stop_flag():
            break

        ja = jitter.sample(rng)
        jb = jitter.sample(rng)

        a_pos = Vec3(base_a.x + ja.x, base_a.y + ja.y, base_a.z + ja.z)
        b_pos = Vec3(base_b.x + jb.x, base_b.y + jb.y, base_b.z + jb.z)

        attacker_eye = attacker.eye_point_at(a_pos)
        target_box = defender.aabb_at(b_pos)

        ev = evaluate_attack(
            attacker_eye=attacker_eye,
            target=target_box,
            solid_blocks=solids,
            reach=float(cfg.reach),
            surface_samples=int(cfg.surface_samples),
            attack_offset=float(cfg.attack_offset),
            attack_samples=int(cfg.attack_samples),
        )

        reachable_any = bool(ev.any_reachable)
        min_dist = float(ev.min_dist)
        surplus = float(cfg.reach - min_dist) if math.isfinite(min_dist) else float("-inf")

        results.append(TrialResult(
            min_dist=min_dist,
            reachable_any=reachable_any,
            surplus=surplus,
            visible_frac=float(ev.visible_frac),
            within_reach_of_visible=float(ev.within_reach_of_visible),
            within_reach_of_total=float(ev.within_reach_of_total),
        ))

        if progress_cb is not None and (i % stride == 0 or i == trials - 1):
            pct = progress_base + progress_span * float(i + 1) / float(trials)
            progress_cb(pct, f"{attacker_name}->{defender_name}", i + 1, trials)

    return results

def run_sim(world: World, jitter: JitterSpec, cfg: SimConfig,
            stop_flag: Callable[[], bool] | None = None,
            progress_cb: ProgressCb | None = None) -> tuple[SummaryStats, SummaryStats, list[TrialResult], list[TrialResult]]:
    """Returns: stats_ab, stats_ba, res_ab, res_ba"""
    res_ab = _one_direction(world, "A", "B", jitter, cfg, progress_cb, 0.0, 50.0, stop_flag)
    stats_ab = summarize(res_ab, cfg.reach)

    if stop_flag is not None and stop_flag():
        if progress_cb is not None:
            progress_cb(50.0, "stopped", len(res_ab), int(cfg.trials))
        return stats_ab, summarize([], cfg.reach), res_ab, []

    res_ba = _one_direction(world, "B", "A", jitter, cfg, progress_cb, 50.0, 50.0, stop_flag)
    stats_ba = summarize(res_ba, cfg.reach)

    if progress_cb is not None:
        progress_cb(100.0, "done", int(cfg.trials), int(cfg.trials))

    return stats_ab, stats_ba, res_ab, res_ba