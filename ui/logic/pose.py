# FILE: ui/logic/pose.py
from __future__ import annotations
import math
from dataclasses import dataclass
from core.geometry.vec3 import Vec3
from core.math.angles import wrap_pi, clamp_pitch
from render.humanoid.model import yaw_to_face, pitch_to_face

@dataclass
class BodyYawFollower:
    """
    Keeps a persistent body yaw state and applies vanilla-like head/body coupling.
    """
    body_yaw: float | None = None

    def reset(self) -> None:
        self.body_yaw = None

    def ensure_initialized(self, foot_pos: Vec3, look_at_pos: Vec3) -> None:
        if self.body_yaw is None:
            self.body_yaw = yaw_to_face(foot_pos, look_at_pos)

    def update(self, desired_head_yaw: float, max_head_body_yaw_deg: float = 75.0) -> float:
        """
        Update body yaw so that |head_yaw - body_yaw| <= max_diff.
        Returns the new body yaw.
        """
        if self.body_yaw is None:
            self.body_yaw = float(desired_head_yaw)
            return self.body_yaw

        max_diff = math.radians(float(max_head_body_yaw_deg))
        cur = float(self.body_yaw)
        diff = wrap_pi(float(desired_head_yaw) - cur)
        if abs(diff) <= max_diff:
            return cur

        self.body_yaw = wrap_pi(float(desired_head_yaw) - (max_diff if diff > 0.0 else -max_diff))
        return float(self.body_yaw)

def compute_head_yaw_pitch(eye: Vec3, aim_target: Vec3) -> tuple[float, float]:
    """
    Compute head yaw/pitch in the humanoid model convention (forward=+Z).
    """
    yaw = yaw_to_face(eye, aim_target)
    pitch = clamp_pitch(pitch_to_face(eye, aim_target))
    return float(yaw), float(pitch)