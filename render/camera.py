# FILE: render/camera.py
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from render.math.transform import rot_yaw_pitch_camera

@dataclass
class Camera:
    pos: np.ndarray  # shape (3,)
    yaw: float       # radians
    pitch: float     # radians
    fov_y: float     # radians
    near: float = 0.1
    far: float = 200.0

    def forward_right_up(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        R = rot_yaw_pitch_camera(self.yaw, self.pitch)
        forward = R @ np.array([0.0, 0.0, -1.0], dtype=np.float64)
        right = R @ np.array([1.0, 0.0, 0.0], dtype=np.float64)
        up = R @ np.array([0.0, 1.0, 0.0], dtype=np.float64)
        return forward, right, up

    def move_local(self, dx: float, dy: float, dz: float) -> None:
        forward, right, up = self.forward_right_up()
        self.pos = self.pos + right * dx + up * dy + forward * dz