# FILE: render/humanoid/skin_uv.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UVRect:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def w(self) -> int:
        return self.x2 - self.x1

    @property
    def h(self) -> int:
        return self.y2 - self.y1

FACES = ("top", "bottom", "right", "front", "left", "back")

# ---- Base layer (regular/Steve style) ----
HEAD_BASE = {
    "top":    UVRect(8, 0, 16, 8),
    "bottom": UVRect(16, 0, 24, 8),
    "right":  UVRect(0, 8, 8, 16),
    "front":  UVRect(8, 8, 16, 16),
    "left":   UVRect(16, 8, 24, 16),
    "back":   UVRect(24, 8, 32, 16),
}

HEAD_OVERLAY = {
    "top":    UVRect(40, 0, 48, 8),
    "bottom": UVRect(48, 0, 56, 8),
    "right":  UVRect(32, 8, 40, 16),
    "front":  UVRect(40, 8, 48, 16),
    "left":   UVRect(48, 8, 56, 16),
    "back":   UVRect(56, 8, 64, 16),
}

TORSO_BASE = {
    "top":    UVRect(20, 16, 28, 20),
    "bottom": UVRect(28, 16, 36, 20),
    "right":  UVRect(16, 20, 20, 32),
    "front":  UVRect(20, 20, 28, 32),
    "left":   UVRect(28, 20, 32, 32),
    "back":   UVRect(32, 20, 40, 32),
}

TORSO_OVERLAY = {
    "top":    UVRect(20, 48, 28, 52),
    "bottom": UVRect(28, 48, 36, 52),
    "right":  UVRect(16, 36, 20, 48),
    "front":  UVRect(20, 36, 28, 48),
    "left":   UVRect(28, 36, 32, 48),
    "back":   UVRect(32, 36, 40, 48),
}

RIGHT_LEG_BASE = {
    "top":    UVRect(4, 16, 8, 20),
    "bottom": UVRect(8, 16, 12, 20),
    "right":  UVRect(0, 20, 4, 32),
    "front":  UVRect(4, 20, 8, 32),
    "left":   UVRect(8, 20, 12, 32),
    "back":   UVRect(12, 20, 16, 32),
}

RIGHT_LEG_OVERLAY = {
    "top":    UVRect(4, 48, 8, 52),
    "bottom": UVRect(8, 48, 12, 52),
    "right":  UVRect(0, 36, 4, 48),
    "front":  UVRect(4, 36, 8, 48),
    "left":   UVRect(8, 36, 12, 48),
    "back":   UVRect(12, 36, 16, 48),
}

LEFT_LEG_BASE = {
    "top":    UVRect(20, 48, 24, 52),
    "bottom": UVRect(24, 48, 28, 52),
    "right":  UVRect(16, 52, 20, 64),
    "front":  UVRect(20, 52, 24, 64),
    "left":   UVRect(24, 52, 28, 64),
    "back":   UVRect(28, 52, 32, 64),
}

LEFT_LEG_OVERLAY = {
    "top":    UVRect(4, 48, 8, 52),
    "bottom": UVRect(8, 48, 12, 52),
    "right":  UVRect(0, 52, 4, 64),
    "front":  UVRect(4, 52, 8, 64),
    "left":   UVRect(8, 52, 12, 64),
    "back":   UVRect(12, 52, 16, 64),
}

RIGHT_ARM_BASE_REGULAR = {
    "top":    UVRect(44, 16, 48, 20),
    "bottom": UVRect(48, 16, 52, 20),
    "right":  UVRect(40, 20, 44, 32),
    "front":  UVRect(44, 20, 48, 32),
    "left":   UVRect(48, 20, 52, 32),
    "back":   UVRect(52, 20, 56, 32),
}

RIGHT_ARM_BASE_SLIM = {
    "top":    UVRect(44, 16, 47, 20),
    "bottom": UVRect(47, 16, 50, 20),
    "right":  UVRect(40, 20, 44, 32),
    "front":  UVRect(44, 20, 47, 32),
    "left":   UVRect(47, 20, 51, 32),
    "back":   UVRect(51, 20, 54, 32),
}

RIGHT_ARM_OVERLAY_REGULAR = {
    "top":    UVRect(44, 48, 48, 52),
    "bottom": UVRect(48, 48, 52, 52),
    "right":  UVRect(40, 36, 44, 48),
    "front":  UVRect(44, 36, 48, 48),
    "left":   UVRect(48, 36, 52, 48),
    "back":   UVRect(52, 36, 56, 48),
}

RIGHT_ARM_OVERLAY_SLIM = {
    "top":    UVRect(44, 48, 47, 52),
    "bottom": UVRect(47, 48, 50, 52),
    "right":  UVRect(40, 36, 44, 48),
    "front":  UVRect(44, 36, 47, 48),
    "left":   UVRect(47, 36, 51, 48),
    "back":   UVRect(51, 36, 54, 48),
}

LEFT_ARM_BASE_REGULAR = {
    "top":    UVRect(36, 48, 40, 52),
    "bottom": UVRect(40, 48, 44, 52),
    "right":  UVRect(32, 52, 36, 64),
    "front":  UVRect(36, 52, 40, 64),
    "left":   UVRect(40, 52, 44, 64),
    "back":   UVRect(44, 52, 48, 64),
}

LEFT_ARM_BASE_SLIM = {
    "top":    UVRect(36, 48, 39, 52),
    "bottom": UVRect(39, 48, 42, 52),
    "right":  UVRect(32, 52, 36, 64),
    "front":  UVRect(36, 52, 39, 64),
    "left":   UVRect(39, 52, 43, 64),
    "back":   UVRect(43, 52, 46, 64),
}

LEFT_ARM_OVERLAY_REGULAR = {
    "top":    UVRect(52, 48, 56, 52),
    "bottom": UVRect(56, 48, 60, 52),
    "right":  UVRect(48, 52, 52, 64),
    "front":  UVRect(52, 52, 56, 64),
    "left":   UVRect(56, 52, 60, 64),
    "back":   UVRect(60, 52, 64, 64),
}

LEFT_ARM_OVERLAY_SLIM = {
    "top":    UVRect(52, 48, 55, 52),
    "bottom": UVRect(55, 48, 58, 52),
    "right":  UVRect(48, 52, 52, 64),
    "front":  UVRect(52, 52, 55, 64),
    "left":   UVRect(55, 52, 59, 64),
    "back":   UVRect(59, 52, 62, 64),
}

def get_base_uv(part: str, face: str, slim_arms: bool) -> UVRect:
    if part == "head":
        return HEAD_BASE[face]
    if part == "torso":
        return TORSO_BASE[face]
    if part == "right_leg":
        return RIGHT_LEG_BASE[face]
    if part == "left_leg":
        return LEFT_LEG_BASE[face]
    if part == "right_arm":
        return (RIGHT_ARM_BASE_SLIM if slim_arms else RIGHT_ARM_BASE_REGULAR)[face]
    if part == "left_arm":
        return (LEFT_ARM_BASE_SLIM if slim_arms else LEFT_ARM_BASE_REGULAR)[face]
    raise KeyError(part)

def get_overlay_uv(part: str, face: str, slim_arms: bool) -> UVRect | None:
    if part == "head":
        return HEAD_OVERLAY[face]
    if part == "torso":
        return TORSO_OVERLAY[face]
    if part == "right_leg":
        return RIGHT_LEG_OVERLAY[face]
    if part == "left_leg":
        return LEFT_LEG_OVERLAY[face]
    if part == "right_arm":
        return (RIGHT_ARM_OVERLAY_SLIM if slim_arms else RIGHT_ARM_OVERLAY_REGULAR)[face]
    if part == "left_arm":
        return (LEFT_ARM_OVERLAY_SLIM if slim_arms else LEFT_ARM_OVERLAY_REGULAR)[face]
    return None