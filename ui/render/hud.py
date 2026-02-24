# FILE: ui/render/hud.py
from __future__ import annotations

import math
from PyQt6.QtGui import QKeySequence

from render.camera import Camera
from ui.qt_utils import mouse_button_name, modifier_name

def _ks(keybinds: dict[str, int], name: str) -> str:
    code = int(keybinds.get(name, 0))
    s = QKeySequence(code).toString()
    return s if s else "?"

def build_hud_top_lines(cam: Camera, keybinds: dict[str, int], mouse_bindings: dict[str, int]) -> list[str]:
    rotate_btn = int(mouse_bindings.get("rotate_button", 0))
    pan_btn = int(mouse_bindings.get("pan_button", 0))
    pan_mod = int(mouse_bindings.get("pan_modifier", 0))

    rotate_txt = mouse_button_name(rotate_btn)
    pan_txt = f"{modifier_name(pan_mod)}+{mouse_button_name(pan_btn)}" if pan_mod != 0 else mouse_button_name(pan_btn)

    return [
        f"Cam pos: ({cam.pos[0]:.2f}, {cam.pos[1]:.2f}, {cam.pos[2]:.2f})",
        f"Yaw/Pitch: ({math.degrees(cam.yaw):.1f} deg, {math.degrees(cam.pitch):.1f} deg)",
        f"Rotate: {rotate_txt} drag | Pan: {pan_txt} drag | Wheel: dolly | "
        f"Move: {_ks(keybinds,'forward')}{_ks(keybinds,'back')}{_ks(keybinds,'left')}{_ks(keybinds,'right')}/"
        f"{_ks(keybinds,'down')}{_ks(keybinds,'up')} | Zoom: {_ks(keybinds,'zoom_in')}/{_ks(keybinds,'zoom_out')}",
    ]