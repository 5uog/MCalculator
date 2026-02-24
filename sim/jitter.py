# FILE: sim/jitter.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from core.geometry.vec3 import Vec3

@dataclass(frozen=True)
class JitterSpec:
    """
    Jitter added to the *foot center position*.
    Default: uniform in [-0.5, 0.5] for x,z; y is 0 (gravity / feet on ground).
    """
    jx: float = 0.5
    jy: float = 0.0
    jz: float = 0.5
    seed: int = 12345

    def rng(self) -> np.random.Generator:
        return np.random.default_rng(self.seed)

    def sample(self, rng: np.random.Generator) -> Vec3:
        dx = rng.uniform(-self.jx, self.jx) if self.jx > 0 else 0.0
        dy = rng.uniform(-self.jy, self.jy) if self.jy > 0 else 0.0
        dz = rng.uniform(-self.jz, self.jz) if self.jz > 0 else 0.0
        return Vec3(float(dx), float(dy), float(dz))