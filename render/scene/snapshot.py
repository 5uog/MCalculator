# FILE: render/scene/snapshot.py
from __future__ import annotations

from dataclasses import dataclass

from core.geometry.vec3 import Vec3
from core.geometry.aabb import AABB

@dataclass(frozen=True)
class BlockViz:
    x: int
    y: int
    z: int
    aabb: AABB
    manual: bool = False

@dataclass(frozen=True)
class PlayerViz:
    name: str
    foot: Vec3
    eye: Vec3
    hitbox: AABB
    model: str = "Steve"

@dataclass(frozen=True)
class AttackViz:
    seg_start: Vec3
    seg_end: Vec3
    aim_target: Vec3
    any_reachable: bool

@dataclass(frozen=True)
class SceneSnapshot:
    player_a: PlayerViz
    player_b: PlayerViz
    blocks: list[BlockViz]
    ground_y: float = 0.0