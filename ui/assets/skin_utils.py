# FILE: ui/assets/skin_utils.py
from __future__ import annotations
from PyQt6.QtGui import QImage, QPixmap

def load_skin_pixmap(path: str) -> QPixmap | None:
    p = str(path).strip()
    if not p:
        return None
    img = QImage(p)
    if img.isNull():
        return None
    return QPixmap.fromImage(img.convertToFormat(QImage.Format.Format_ARGB32))