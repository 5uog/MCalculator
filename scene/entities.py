# FILE: scene/entities.py
from __future__ import annotations
from dataclasses import dataclass
from core.geometry.vec3 import Vec3
from core.geometry.aabb import AABB

STEVE_GEOMETRY = "geometry.humanoid.custom"
ALEX_GEOMETRY = "geometry.humanoid.customSlim"

@dataclass
class Player:
    name: str
    pos: Vec3  # foot center

    width: float = 0.6
    height: float = 1.8
    eye: float = 1.62

    model: str = "Steve"      # "Steve" | "Alex"
    geometry: str = STEVE_GEOMETRY

    def aabb_at(self, pos: Vec3) -> AABB:
        """Compute the hitbox AABB for an arbitrary foot-center position."""
        hw = float(self.width) / 2.0
        mn = Vec3(pos.x - hw, pos.y, pos.z - hw)
        mx = Vec3(pos.x + hw, pos.y + float(self.height), pos.z + hw)
        return AABB(mn, mx)

    def eye_point_at(self, pos: Vec3) -> Vec3:
        """Compute the eye point for an arbitrary foot-center position."""
        return Vec3(pos.x, pos.y + float(self.eye), pos.z)

    def aabb(self) -> AABB:
        return self.aabb_at(self.pos)

    def foot_point(self) -> Vec3:
        return self.pos

    def eye_point(self) -> Vec3:
        return self.eye_point_at(self.pos)

@dataclass(frozen=True)
class Block:
    x: int
    y: int
    z: int
    manual: bool = False

    def aabb(self) -> AABB:
        mn = Vec3(float(self.x), float(self.y), float(self.z))
        mx = Vec3(float(self.x + 1), float(self.y + 1), float(self.z + 1))
        return AABB(mn, mx)