# FILE: ui/assets/image_utils.py
from __future__ import annotations

from pathlib import Path
from PyQt6.QtGui import QImage, QPixmap

def load_png_pixmap(path: str | Path) -> QPixmap | None:
    """
    Load a PNG file into a QPixmap in a stable ARGB32 format.
    Returns None if the image cannot be loaded.
    """
    p = str(path).strip()
    if not p:
        return None

    img = QImage(p)
    if img.isNull():
        return None

    return QPixmap.fromImage(img.convertToFormat(QImage.Format.Format_ARGB32))