# FILE: ui/widgets/viewport3d.py
from __future__ import annotations

import time
import numpy as np

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget

from render.camera import Camera
from render.scene.items import RenderItem
from ui.controllers.camera_controller import CameraController
from ui.render.viewport_renderer import ViewportRenderer
from ui.render.hud import build_hud_top_lines
from utils.qt import enum_int

class Viewport3D(QWidget):
    def __init__(self, texture_resolver, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.cam = Camera(
            pos=np.array([8.0, 6.0, 12.0], dtype=np.float64),
            yaw=float(np.deg2rad(-135.0)),
            pitch=float(np.deg2rad(-25.0)),
            fov_y=float(np.deg2rad(60.0)),
            near=0.1,
            far=200.0,
        )

        # Defaults are stored in config; widget applies them via controller.
        self._controller = CameraController(
            cam=self.cam,
            keybinds={},
            rotate_button=0,
            pan_button=0,
            pan_modifier=0,
        )

        self._renderer = ViewportRenderer(texture_resolver)
        self.items: list[RenderItem] = []

        self._fps_display = 0.0
        self._fps_last_t = time.perf_counter()
        self._fps_accum_s = 0.0
        self._fps_frames = 0
        self._fps_window_s = 0.5

        self._tick = QTimer(self)
        self._tick.setInterval(16)  # ~60Hz
        self._tick.timeout.connect(self.update)
        self._tick.start()

    # ----- State getters/setters for persistence -----
    def get_keybinds(self) -> dict[str, int]:
        return self._controller.get_keybinds()

    def set_keybinds(self, binds: dict[str, int]) -> None:
        self._controller.set_keybinds(binds)

    def get_mouse_bindings(self) -> dict[str, int]:
        return self._controller.get_mouse_bindings()

    def set_mouse_bindings(self, mb: dict[str, int]) -> None:
        self._controller.set_mouse_bindings(mb)

    def set_control_tunings(self, mouse_sens: float, pan_sens: float, move_speed: float, zoom_step: float, wheel_factor: float) -> None:
        self._controller.set_tunings(mouse_sens, pan_sens, move_speed, zoom_step, wheel_factor)

    def get_camera_state(self) -> dict[str, object]:
        return {
            "pos": [float(self.cam.pos[0]), float(self.cam.pos[1]), float(self.cam.pos[2])],
            "yaw": float(self.cam.yaw),
            "pitch": float(self.cam.pitch),
            "fov_y": float(self.cam.fov_y),
            "near": float(self.cam.near),
            "far": float(self.cam.far),
        }

    def set_camera_state(self, pos: np.ndarray, yaw: float, pitch: float, fov_y: float, near: float, far: float) -> None:
        self.cam.pos = pos.astype(np.float64)
        self.cam.yaw = float(yaw)
        self.cam.pitch = float(pitch)
        self.cam.fov_y = float(fov_y)
        self.cam.near = float(near)
        self.cam.far = float(far)
        self.update()

    # ----- Scene update -----
    def look_at(self, target: np.ndarray) -> None:
        self.cam.yaw, self.cam.pitch = CameraController.yaw_pitch_look_at(self.cam.pos, target)
        self.update()

    def set_scene(self, items: list[RenderItem]) -> None:
        self.items = items
        self.update()

    # ----- Qt events -----
    def mousePressEvent(self, e):
        btn = enum_int(e.button())
        mods = enum_int(e.modifiers())
        pos = (float(e.position().x()), float(e.position().y()))

        if self._controller.on_mouse_press(btn, mods, pos):
            if self._controller.mode() == "pan":
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            elif self._controller.mode() == "rotate":
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.update()
            return

    def mouseReleaseEvent(self, e):
        btn = enum_int(e.button())
        if self._controller.on_mouse_release(btn):
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            return

    def mouseMoveEvent(self, e):
        pos = (float(e.position().x()), float(e.position().y()))
        if self._controller.on_mouse_move(pos):
            self.update()
            return

    def wheelEvent(self, e):
        delta = float(e.angleDelta().y())
        if self._controller.on_wheel(delta):
            self.update()
            return

    def keyPressEvent(self, e):
        key_code = enum_int(e.key())
        mods_mask = enum_int(e.modifiers())
        combo = mods_mask | key_code

        if self._controller.on_key_combo(int(combo)):
            self.update()
            return

    def paintEvent(self, _):
        now = time.perf_counter()
        dt = now - self._fps_last_t
        self._fps_last_t = now
        if dt < 0.0:
            dt = 0.0

        self._fps_accum_s += dt
        self._fps_frames += 1

        if self._fps_accum_s >= self._fps_window_s:
            fps = float(self._fps_frames) / float(self._fps_accum_s) if self._fps_accum_s > 1e-9 else 0.0
            self._fps_display = max(0.0, min(999.0, fps))
            self._fps_accum_s = 0.0
            self._fps_frames = 0

        w, h = max(1, self.width()), max(1, self.height())
        painter = QPainter(self)

        hud_top = build_hud_top_lines(self.cam, self.get_keybinds(), self.get_mouse_bindings())
        fps_text = f"FPS: {self._fps_display:.1f}"

        self._renderer.draw(painter, self.cam, self.items, hud_top, fps_text, w, h)
        painter.end()