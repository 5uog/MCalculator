# FILE: core/metrics/summary.py
from __future__ import annotations
import numpy as np
from core.metrics.types import TrialResult, SummaryStats

def summarize(results: list[TrialResult], reach: float) -> SummaryStats:
    n = len(results)
    if n == 0:
        return SummaryStats(
            0, reach,
            0.0,
            float("nan"), float("nan"),
            float("nan"), float("nan"), float("nan"),
            float("nan"), float("nan"),
            float("nan"), float("nan"),
        )

    dists = np.array([r.min_dist for r in results], dtype=np.float64)
    surp = np.array([r.surplus for r in results], dtype=np.float64)

    hit_any = float(np.mean([1.0 if r.reachable_any else 0.0 for r in results]))

    vis = np.array([r.visible_frac for r in results], dtype=np.float64)
    within_vis = np.array([r.within_reach_of_visible for r in results], dtype=np.float64)
    within_total = np.array([r.within_reach_of_total for r in results], dtype=np.float64)

    return SummaryStats(
        n=n,
        reach=reach,
        hit_prob_any=hit_any,
        mean_dist=float(np.mean(dists)),
        mean_surplus=float(np.mean(surp)),
        p10_dist=float(np.percentile(dists, 10)),
        p50_dist=float(np.percentile(dists, 50)),
        p90_dist=float(np.percentile(dists, 90)),
        mean_visible_frac=float(np.mean(vis)),
        mean_occluded_frac=float(np.mean(1.0 - vis)),
        mean_within_reach_of_visible=float(np.mean(within_vis)),
        mean_within_reach_of_total=float(np.mean(within_total)),
    )