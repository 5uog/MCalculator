# FILE: ui/state/default_controls.py
from __future__ import annotations

from PyQt6.QtCore import Qt

from utils.qt import enum_int

DEFAULT_KEYBINDS: dict[str, int] = {
    "forward": enum_int(Qt.Key.Key_W),
    "back": enum_int(Qt.Key.Key_S),
    "left": enum_int(Qt.Key.Key_A),
    "right": enum_int(Qt.Key.Key_D),
    "down": enum_int(Qt.Key.Key_Q),
    "up": enum_int(Qt.Key.Key_E),
    "zoom_in": enum_int(Qt.Key.Key_C),
    "zoom_out": enum_int(Qt.Key.Key_X),
}

DEFAULT_MOUSE: dict[str, int] = {
    "rotate_button": enum_int(Qt.MouseButton.RightButton),
    "pan_button": enum_int(Qt.MouseButton.RightButton),
    "pan_modifier": enum_int(Qt.KeyboardModifier.ControlModifier),
}