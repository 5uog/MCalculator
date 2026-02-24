# FILE: ui/controllers/camera_controller.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from render.camera import Camera
from utils.numeric import clampf

@dataclass
class CameraController:
    """
    Input/controller logic for a 3D camera.
    This module is Qt-agnostic; the widget adapts Qt events to this API.
    """
    cam: Camera

    keybinds: dict[str, int]
    rotate_button: int
    pan_button: int
    pan_modifier: int

    mouse_sens: float = 0.005
    pan_sens: float = 0.012
    move_speed: float = 0.45
    zoom_step: float = 0.24
    wheel_dolly_factor: float = 0.002

    # Invert Y-Axis:
    #   False => mouse up looks up
    #   True  => mouse up looks down
    invert_y: bool = False

    _last_mouse: Optional[tuple[float, float]] = None
    _mode: Optional[str] = None  # "rotate" | "pan" | None

    def get_keybinds(self) -> dict[str, int]:
        return dict(self.keybinds)

    def set_keybinds(self, binds: dict[str, int]) -> None:
        for k in ("forward", "back", "left", "right", "down", "up", "zoom_in", "zoom_out"):
            if k in binds:
                self.keybinds[k] = int(binds[k])

    def get_mouse_bindings(self) -> dict[str, int]:
        return {
            "rotate_button": int(self.rotate_button),
            "pan_button": int(self.pan_button),
            "pan_modifier": int(self.pan_modifier),
        }

    def set_mouse_bindings(self, mb: dict[str, int]) -> None:
        if "rotate_button" in mb:
            self.rotate_button = int(mb["rotate_button"])
        if "pan_button" in mb:
            self.pan_button = int(mb["pan_button"])
        if "pan_modifier" in mb:
            self.pan_modifier = int(mb["pan_modifier"])

    def set_tunings(
        self,
        mouse_sens: float,
        pan_sens: float,
        move_speed: float,
        zoom_step: float,
        wheel_factor: float,
        invert_y: bool,
    ) -> None:
        self.mouse_sens = float(mouse_sens)
        self.pan_sens = float(pan_sens)
        self.move_speed = float(move_speed)
        self.zoom_step = float(zoom_step)
        self.wheel_dolly_factor = float(wheel_factor)
        self.invert_y = bool(invert_y)

    def mode(self) -> Optional[str]:
        return self._mode

    def on_mouse_press(self, btn: int, mods: int, pos: tuple[float, float]) -> bool:
        if btn == int(self.pan_button):
            if self.pan_modifier == 0 or (mods & int(self.pan_modifier)) == int(self.pan_modifier):
                self._last_mouse = (float(pos[0]), float(pos[1]))
                self._mode = "pan"
                return True

        if btn == int(self.rotate_button):
            self._last_mouse = (float(pos[0]), float(pos[1]))
            self._mode = "rotate"
            return True

        return False

    def on_mouse_release(self, btn: int) -> bool:
        if btn == int(self.rotate_button) or btn == int(self.pan_button):
            self._last_mouse = None
            self._mode = None
            return True
        return False

    def on_mouse_move(self, pos: tuple[float, float]) -> bool:
        if self._last_mouse is None or self._mode is None:
            return False

        x, y = float(pos[0]), float(pos[1])
        lx, ly = self._last_mouse
        dx = x - lx
        dy = y - ly
        self._last_mouse = (x, y)

        if self._mode == "rotate":
            s = float(self.mouse_sens)

            # Fix: horizontal (yaw) sign.
            # Mouse right should turn view right => use "-dx" in this camera convention.
            self.cam.yaw -= dx * s

            # Vertical (pitch): keep as-is (you said this is now correct).
            # dy < 0 means mouse moved up.
            # invert_y=False => mouse up looks up => pitch += (-dy)*s
            # invert_y=True  => mouse up looks down => pitch += (+dy)*s
            self.cam.pitch += (dy if self.invert_y else -dy) * s
            self.cam.pitch = clampf(self.cam.pitch, math.radians(-89.0), math.radians(89.0))
            return True

        if self._mode == "pan":
            self.cam.move_local(-dx * float(self.pan_sens), dy * float(self.pan_sens), 0.0)
            return True

        return False

    def on_wheel(self, delta_y: float) -> bool:
        self.cam.move_local(0.0, 0.0, -float(delta_y) * float(self.wheel_dolly_factor))
        return True

    def on_key_combo(self, combo: int) -> bool:
        if combo == int(self.keybinds.get("forward", 0)):
            self.cam.move_local(0.0, 0.0, +self.move_speed)
            return True
        if combo == int(self.keybinds.get("back", 0)):
            self.cam.move_local(0.0, 0.0, -self.move_speed)
            return True
        if combo == int(self.keybinds.get("left", 0)):
            self.cam.move_local(-self.move_speed, 0.0, 0.0)
            return True
        if combo == int(self.keybinds.get("right", 0)):
            self.cam.move_local(self.move_speed, 0.0, 0.0)
            return True
        if combo == int(self.keybinds.get("down", 0)):
            self.cam.move_local(0.0, -self.move_speed, 0.0)
            return True
        if combo == int(self.keybinds.get("up", 0)):
            self.cam.move_local(0.0, self.move_speed, 0.0)
            return True
        if combo == int(self.keybinds.get("zoom_in", 0)):
            self.cam.move_local(0.0, 0.0, +self.zoom_step)
            return True
        if combo == int(self.keybinds.get("zoom_out", 0)):
            self.cam.move_local(0.0, 0.0, -self.zoom_step)
            return True
        return False

    @staticmethod
    def yaw_pitch_look_at(cam_pos: np.ndarray, target: np.ndarray) -> tuple[float, float]:
        v = target.astype(np.float64) - cam_pos.astype(np.float64)
        n = float(np.linalg.norm(v))
        if n <= 1e-12:
            return 0.0, 0.0
        f = v / n
        fy = float(clampf(float(f[1]), -1.0, 1.0))
        pitch = math.asin(fy)
        cp = math.cos(pitch)
        if abs(cp) < 1e-9:
            yaw = 0.0
        else:
            fx = float(f[0])
            fz = float(f[2])
            yaw = math.atan2(-fx, -fz)
        pitch = clampf(pitch, math.radians(-89.0), math.radians(89.0))
        return float(yaw), float(pitch)