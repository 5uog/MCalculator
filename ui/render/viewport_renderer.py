# FILE: ui/render/viewport_renderer.py
from __future__ import annotations

import math
import numpy as np

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QTransform,
    QPainterPath, QPolygonF
)

from render.camera import Camera
from render.projection import (
    view_matrix, proj_matrix_perspective,
    world_to_camera, project_cam_to_screen, project_segment_world
)
from core.geometry.aabb import AABB
from render.scene.items import RenderItem

from utils.numeric import clamp01, finite_or


def _aabb_edges() -> list[tuple[int, int]]:
    return [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]


class ViewportRenderer:
    """
    All rendering logic for the 3D viewport.
    Qt drawing stays here; items are Qt-agnostic.
    """

    def __init__(self, texture_resolver):
        # texture_resolver(key:str) -> QPixmap | None
        self._tex = texture_resolver

        self.grid_half_size = 50
        self.grid_step = 1
        self.ground_y = 0.0

    def draw(self, painter: QPainter, cam: Camera, items: list[RenderItem], hud_top: list[str], fps_text: str, w: int, h: int) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        painter.fillRect(painter.viewport(), painter.device().palette().window() if hasattr(painter.device(), "palette") else QColor(30, 30, 30))

        V = view_matrix(cam.pos, cam.yaw, cam.pitch)
        P = proj_matrix_perspective(cam.fov_y, w / h, cam.near, cam.far)

        self._draw_ground_grid(painter, V, P, cam, w, h)
        self._draw_axes(painter, V, P, cam, w, h)

        tex = [it for it in items if it.kind == "tex_quad" and it.verts is not None and it.texture_key]
        aabbs = [it for it in items if it.kind == "aabb" and it.aabb is not None]
        segs = [it for it in items if it.kind == "segment" and it.a is not None and it.b is not None]
        crosses = [it for it in items if it.kind == "cross" and it.p is not None]

        sortable_quads = []
        for it in tex:
            zavg = self._quad_avg_cam_z(it, cam, V)
            if zavg is None:
                continue
            if not self._quad_faces_camera(it, cam):
                continue
            sortable_quads.append((zavg, it))
        sortable_quads.sort(key=lambda t: t[0])

        for _, it in sortable_quads:
            self._draw_tex_quad(painter, it, cam, V, P, w, h)

        sortable = []
        for it in aabbs:
            c = self._aabb_center_np(it.aabb)  # type: ignore[arg-type]
            cc = (V @ np.array([c[0], c[1], c[2], 1.0], dtype=np.float64).reshape(4, 1)).reshape(4)
            sortable.append((float(cc[2]), it))
        sortable.sort(key=lambda t: t[0])

        for _, it in sortable:
            self._draw_aabb_wire(painter, it, cam, V, P, w, h)

        for it in segs:
            painter.setPen(QPen(self._qcolor(it.color), 2))
            self._draw_segment_world(painter, it.a, it.b, V, P, w, h, cam.near)

        for it in crosses:
            self._draw_cross_world(painter, it, cam, V, P, w, h)

        self._draw_hud(painter, hud_top, fps_text, w, h)

    def _qcolor(self, rgb: tuple[int, int, int]) -> QColor:
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        return QColor(r, g, b)

    def _quad_faces_camera(self, it: RenderItem, cam: Camera) -> bool:
        if it.normal is None or it.verts is None:
            return True
        c = np.mean(it.verts, axis=0)
        to_cam = cam.pos - c
        return float(np.dot(it.normal, to_cam)) > 0.0

    def _quad_avg_cam_z(self, it: RenderItem, cam: Camera, V: np.ndarray) -> float | None:
        assert it.verts is not None
        zs = []
        for p in it.verts:
            pc = world_to_camera(V, p)
            z = float(pc[2])
            if z > -float(cam.near):
                return None
            zs.append(z)
        return float(sum(zs) / len(zs))

    def _homography_to_qtransform(self, src: list[tuple[float, float]], dst: list[tuple[float, float]]) -> QTransform | None:
        if len(src) != 4 or len(dst) != 4:
            return None

        A = np.zeros((8, 8), dtype=np.float64)
        b = np.zeros((8,), dtype=np.float64)

        for i, ((x, y), (u, v)) in enumerate(zip(src, dst)):
            r = 2 * i
            A[r, 0] = x
            A[r, 1] = y
            A[r, 2] = 1.0
            A[r, 6] = -u * x
            A[r, 7] = -u * y
            b[r] = u

            A[r + 1, 3] = x
            A[r + 1, 4] = y
            A[r + 1, 5] = 1.0
            A[r + 1, 6] = -v * x
            A[r + 1, 7] = -v * y
            b[r + 1] = v

        try:
            h = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            return None

        h11, h12, h13, h21, h22, h23, h31, h32 = [float(x) for x in h]

        return QTransform(
            h11, h21, h31,
            h12, h22, h32,
            h13, h23, 1.0
        )

    def _draw_tex_quad(self, painter: QPainter, it: RenderItem, cam: Camera, V: np.ndarray, P: np.ndarray, w: int, h: int) -> None:
        assert it.verts is not None and it.texture_key

        pm = self._tex(str(it.texture_key))
        if pm is None:
            return

        dst_pts: list[tuple[float, float]] = []
        for p in it.verts:
            pc = world_to_camera(V, p)
            if float(pc[2]) > -float(cam.near):
                return
            sp = project_cam_to_screen(pc, P, w, h)
            if sp is None:
                return
            dst_pts.append((float(sp[0]), float(sp[1])))

        if it.src_rect is None:
            src = QRectF(0.0, 0.0, float(pm.width()), float(pm.height()))
        else:
            x, y, ww, hh = it.src_rect
            src = QRectF(float(x), float(y), float(ww), float(hh))

        sw = float(src.width())
        sh = float(src.height())
        if sw <= 1e-6 or sh <= 1e-6:
            return

        src_pts = [(0.0, 0.0), (sw, 0.0), (sw, sh), (0.0, sh)]
        xf = self._homography_to_qtransform(src_pts, dst_pts)
        if xf is None:
            return

        op = clamp01(finite_or(it.opacity, 1.0))

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.setTransform(xf, False)
        painter.setOpacity(float(op))

        inv, ok = xf.inverted()
        if ok:
            poly_dst = QPolygonF([QPointF(x, y) for (x, y) in dst_pts])
            poly_src = inv.map(poly_dst)
            path = QPainterPath()
            path.addPolygon(poly_src)
            painter.setClipPath(path, Qt.ClipOperation.ReplaceClip)

        painter.drawPixmap(QRectF(0.0, 0.0, sw, sh), pm, src)
        painter.restore()

    def _aabb_center_np(self, box: AABB) -> np.ndarray:
        return np.array([
            (box.mn.x + box.mx.x) * 0.5,
            (box.mn.y + box.mx.y) * 0.5,
            (box.mn.z + box.mx.z) * 0.5,
        ], dtype=np.float64)

    def _draw_segment_world(self, painter: QPainter, a: np.ndarray, b: np.ndarray,
                            V: np.ndarray, P: np.ndarray, w: int, h: int, near: float) -> None:
        seg = project_segment_world(a, b, V, P, w, h, near)
        if seg is None:
            return
        pa, pb = seg
        painter.drawLine(QPointF(float(pa[0]), float(pa[1])), QPointF(float(pb[0]), float(pb[1])))

    def _project_point_world(self, p_world: np.ndarray, V: np.ndarray, P: np.ndarray, w: int, h: int, near: float) -> np.ndarray | None:
        pc = world_to_camera(V, p_world)
        if float(pc[2]) > -float(near):
            return None
        return project_cam_to_screen(pc, P, w, h)

    def _draw_cross_world(self, painter: QPainter, it: RenderItem, cam: Camera, V: np.ndarray, P: np.ndarray, w: int, h: int) -> None:
        assert it.p is not None
        p2 = self._project_point_world(it.p, V, P, w, h, cam.near)
        if p2 is None:
            return
        x = float(p2[0])
        y = float(p2[1])
        s = float(it.size_px) * 0.5
        painter.setPen(QPen(self._qcolor(it.color), 3))
        painter.drawLine(QPointF(x - s, y - s), QPointF(x + s, y + s))
        painter.drawLine(QPointF(x - s, y + s), QPointF(x + s, y - s))

    def _draw_aabb_wire(self, painter: QPainter, it: RenderItem, cam: Camera, V: np.ndarray, P: np.ndarray, w: int, h: int) -> None:
        assert it.aabb is not None
        corners = it.aabb.corners()
        pts = np.array([[c.x, c.y, c.z] for c in corners], dtype=np.float64)

        painter.setPen(QPen(self._qcolor(it.color), 2))
        for i, j in _aabb_edges():
            a = pts[i]
            b = pts[j]
            self._draw_segment_world(painter, a, b, V, P, w, h, cam.near)

        if not it.label:
            return

        label_world = pts[6]
        p2 = self._project_point_world(label_world, V, P, w, h, cam.near)
        if p2 is None:
            return

        painter.setPen(QPen(self._qcolor(it.color), 1))
        painter.setFont(QFont("Sans Serif", 10))

        x0 = float(p2[0] + 4.0)
        y0 = float(p2[1] - 4.0)

        lines = it.label.splitlines()
        for idx, line in enumerate(lines):
            painter.drawText(QPointF(x0, y0 + float(idx * 12)), line)

    def _draw_ground_grid(self, painter: QPainter, V: np.ndarray, P: np.ndarray, cam: Camera, w: int, h: int) -> None:
        g = int(self.grid_half_size)
        step = int(self.grid_step)
        y = float(self.ground_y)

        minor = QColor(110, 110, 110)
        major = QColor(140, 140, 140)

        for i in range(-g, g + 1, step):
            col = major if (i % 5 == 0) else minor
            painter.setPen(QPen(col, 1))

            a = np.array([float(i), y, float(-g)], dtype=np.float64)
            b = np.array([float(i), y, float(g)], dtype=np.float64)
            self._draw_segment_world(painter, a, b, V, P, w, h, cam.near)

            a = np.array([float(-g), y, float(i)], dtype=np.float64)
            b = np.array([float(g), y, float(i)], dtype=np.float64)
            self._draw_segment_world(painter, a, b, V, P, w, h, cam.near)

        painter.setPen(QPen(QColor(170, 170, 170), 2))
        self._draw_segment_world(
            painter,
            np.array([float(-g), y, 0.0], dtype=np.float64),
            np.array([float(g), y, 0.0], dtype=np.float64),
            V, P, w, h, cam.near
        )
        self._draw_segment_world(
            painter,
            np.array([0.0, y, float(-g)], dtype=np.float64),
            np.array([0.0, y, float(g)], dtype=np.float64),
            V, P, w, h, cam.near
        )

    def _draw_arrow_world(self, painter: QPainter, a: np.ndarray, b: np.ndarray, V: np.ndarray, P: np.ndarray, w: int, h: int, near: float, arrow_len_px: float = 10.0) -> None:
        seg = project_segment_world(a, b, V, P, w, h, near)
        if seg is None:
            return
        pa, pb = seg

        x0, y0 = float(pa[0]), float(pa[1])
        x1, y1 = float(pb[0]), float(pb[1])

        painter.drawLine(QPointF(x0, y0), QPointF(x1, y1))

        dx = x1 - x0
        dy = y1 - y0
        L = math.hypot(dx, dy)
        if L < 1e-6:
            return

        ux = dx / L
        uy = dy / L

        px = -uy
        py = ux

        al = float(arrow_len_px)
        aw = al * 0.45

        bx = x1 - ux * al
        by = y1 - uy * al

        p1x = bx + px * aw
        p1y = by + py * aw
        p2x = bx - px * aw
        p2y = by - py * aw

        painter.drawLine(QPointF(x1, y1), QPointF(p1x, p1y))
        painter.drawLine(QPointF(x1, y1), QPointF(p2x, p2y))

    def _draw_axes(self, painter: QPainter, V: np.ndarray, P: np.ndarray, cam: Camera, w: int, h: int) -> None:
        L = 4.0
        painter.setPen(QPen(QColor(220, 80, 80), 2))
        self._draw_arrow_world(painter, np.array([0.0, 0.0, 0.0]), np.array([L, 0.0, 0.0]), V, P, w, h, cam.near)
        painter.setPen(QPen(QColor(80, 220, 80), 2))
        self._draw_arrow_world(painter, np.array([0.0, 0.0, 0.0]), np.array([0.0, L, 0.0]), V, P, w, h, cam.near)
        painter.setPen(QPen(QColor(80, 140, 220), 2))
        self._draw_arrow_world(painter, np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, L]), V, P, w, h, cam.near)

    def _draw_hud(self, painter: QPainter, top_lines: list[str], fps_text: str, w: int, h: int) -> None:
        painter.setPen(QPen(painter.pen().color(), 1))
        painter.setFont(QFont("Consolas", 9))

        x = 10
        y = 18
        for line in top_lines:
            painter.drawText(x, y, line)
            y += 14

        painter.drawText(10, h - 10, fps_text)