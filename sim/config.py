# FILE: sim/config.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SimConfig:
    reach: float = 3.0
    trials: int = 5000

    surface_samples: int = 15  # per edge per face
    attack_offset: float = 0.8
    attack_samples: int = 9