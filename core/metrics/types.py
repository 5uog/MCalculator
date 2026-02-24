# FILE: core/metrics/types.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TrialResult:
    min_dist: float
    reachable_any: bool
    surplus: float  # reach - min_dist (can be negative or inf)
    visible_frac: float  # visible_points / total_points
    within_reach_of_visible: float  # reachable_visible / visible_points
    within_reach_of_total: float  # reachable_visible / total_points

@dataclass(frozen=True)
class SummaryStats:
    n: int
    reach: float

    hit_prob_any: float

    mean_dist: float
    mean_surplus: float
    p10_dist: float
    p50_dist: float
    p90_dist: float

    mean_visible_frac: float
    mean_occluded_frac: float
    mean_within_reach_of_visible: float
    mean_within_reach_of_total: float