# FILE: core/geometry/aabb.py
from __future__ import annotations
from dataclasses import dataclass
import math
from core.geometry.vec3 import Vec3
from core.math.scalar import clamp

@dataclass(frozen=True)
class AABB:
    """Axis-aligned bounding box: [min, max] in each axis."""
    mn: Vec3
    mx: Vec3

    def contains(self, p: Vec3) -> bool:
        return (self.mn.x <= p.x <= self.mx.x and
                self.mn.y <= p.y <= self.mx.y and
                self.mn.z <= p.z <= self.mx.z)

    def closest_point(self, p: Vec3) -> Vec3:
        return Vec3(
            clamp(p.x, self.mn.x, self.mx.x),
            clamp(p.y, self.mn.y, self.mx.y),
            clamp(p.z, self.mn.z, self.mx.z),
        )

    def distance_to_point(self, p: Vec3) -> float:
        c = self.closest_point(p)
        dx = p.x - c.x
        dy = p.y - c.y
        dz = p.z - c.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def corners(self) -> list[Vec3]:
        mn, mx = self.mn, self.mx
        return [
            Vec3(mn.x, mn.y, mn.z), Vec3(mx.x, mn.y, mn.z),
            Vec3(mx.x, mx.y, mn.z), Vec3(mn.x, mx.y, mn.z),
            Vec3(mn.x, mn.y, mx.z), Vec3(mx.x, mn.y, mx.z),
            Vec3(mx.x, mx.y, mx.z), Vec3(mn.x, mx.y, mx.z),
        ]