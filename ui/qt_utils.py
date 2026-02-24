# FILE: ui/qt_utils.py
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

def enum_int(v) -> int:
    """
    Convert PyQt6 enums / flags to a plain int safely.
    QFlags may not be int()-convertible; they expose `.value`.
    """
    try:
        return int(v)
    except TypeError:
        pass
    if hasattr(v, "value"):
        try:
            return int(v.value)
        except Exception:
            return 0
    return 0

def keyseq_to_int(seq: QKeySequence) -> int:
    """
    Convert QKeySequenceEdit result to a single "combined int".
    combined = modifiers_bitmask | key_code
    """
    try:
        cnt = seq.count()
    except Exception:
        cnt = 0
    if cnt <= 0:
        return 0

    try:
        first = seq[0]
    except Exception:
        return 0

    if hasattr(first, "toCombined"):
        try:
            return int(first.toCombined())
        except Exception:
            return 0

    try:
        return int(first)
    except Exception:
        return 0

def mouse_button_name(btn: int) -> str:
    if btn == enum_int(Qt.MouseButton.LeftButton):
        return "LMB"
    if btn == enum_int(Qt.MouseButton.MiddleButton):
        return "MMB"
    if btn == enum_int(Qt.MouseButton.RightButton):
        return "RMB"
    return "Mouse"

def modifier_name(mask: int) -> str:
    if mask == 0:
        return "None"
    if mask == enum_int(Qt.KeyboardModifier.ControlModifier):
        return "Ctrl"
    if mask == enum_int(Qt.KeyboardModifier.ShiftModifier):
        return "Shift"
    if mask == enum_int(Qt.KeyboardModifier.AltModifier):
        return "Alt"
    if mask == enum_int(Qt.KeyboardModifier.MetaModifier):
        return "Meta"

    parts: list[str] = []
    if mask & enum_int(Qt.KeyboardModifier.ControlModifier):
        parts.append("Ctrl")
    if mask & enum_int(Qt.KeyboardModifier.ShiftModifier):
        parts.append("Shift")
    if mask & enum_int(Qt.KeyboardModifier.AltModifier):
        parts.append("Alt")
    if mask & enum_int(Qt.KeyboardModifier.MetaModifier):
        parts.append("Meta")
    return "+".join(parts) if parts else "Mod"