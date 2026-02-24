# FILE: render/projection.py
from __future__ import annotations
import math
import numpy as np
from render.math.transform import rot_yaw_pitch_camera

def view_matrix(cam_pos: np.ndarray, yaw: float, pitch: float) -> np.ndarray:
    """
    World -> Camera (right-handed). Camera looks toward -Z.
    """
    R = rot_yaw_pitch_camera(yaw, pitch)
    Rt = R.T
    t = -Rt @ cam_pos.reshape(3, 1)

    M = np.eye(4, dtype=np.float64)
    M[:3, :3] = Rt
    M[:3, 3:4] = t
    return M

def proj_matrix_perspective(fov_y: float, aspect: float, near: float, far: float) -> np.ndarray:
    """
    OpenGL-like perspective projection (right-handed, camera forward = -Z).
    """
    f = 1.0 / math.tan(fov_y / 2.0)
    M = np.zeros((4, 4), dtype=np.float64)
    M[0, 0] = f / aspect
    M[1, 1] = f
    M[2, 2] = (far + near) / (near - far)
    M[2, 3] = (2 * far * near) / (near - far)
    M[3, 2] = -1.0
    return M

def world_to_camera(V: np.ndarray, p_world: np.ndarray) -> np.ndarray:
    """
    p_world: (3,)
    returns p_cam: (3,) in camera space
    """
    pw = np.array([p_world[0], p_world[1], p_world[2], 1.0], dtype=np.float64)
    pc = V @ pw
    return pc[:3].copy()

def clip_segment_to_near(p0_cam: np.ndarray, p1_cam: np.ndarray, near: float) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Clip a segment in camera space against the near plane z = -near.
    Camera forward is -Z, so visible region satisfies z <= -near.
    Returns (visible, new_p0, new_p1).
    """
    z0 = float(p0_cam[2])
    z1 = float(p1_cam[2])
    z_plane = -float(near)

    inside0 = (z0 <= z_plane)
    inside1 = (z1 <= z_plane)

    if inside0 and inside1:
        return True, p0_cam, p1_cam

    if (not inside0) and (not inside1):
        return False, p0_cam, p1_cam

    dz = z1 - z0
    if abs(dz) < 1e-12:
        return False, p0_cam, p1_cam

    t = (z_plane - z0) / dz
    t = max(0.0, min(1.0, t))
    pi = p0_cam + (p1_cam - p0_cam) * t

    if inside0 and (not inside1):
        return True, p0_cam, pi
    else:
        return True, pi, p1_cam

def project_cam_to_screen(p_cam: np.ndarray, P: np.ndarray, w: int, h: int) -> np.ndarray | None:
    """
    Project a camera-space point to screen space.
    Returns (x,y) or None if invalid (w ~ 0).
    """
    pc = np.array([p_cam[0], p_cam[1], p_cam[2], 1.0], dtype=np.float64)
    clip = P @ pc
    cw = float(clip[3])
    if abs(cw) < 1e-12:
        return None
    ndc = clip[:3] / cw
    x = (ndc[0] * 0.5 + 0.5) * w
    y = (1.0 - (ndc[1] * 0.5 + 0.5)) * h
    return np.array([x, y], dtype=np.float64)

def project_segment_world(a_world: np.ndarray, b_world: np.ndarray, V: np.ndarray, P: np.ndarray, w: int, h: int, near: float) -> tuple[np.ndarray, np.ndarray] | None:
    """
    World-space segment -> (screen_a, screen_b) after near-plane clipping.
    Returns None if fully invisible.
    """
    a_cam = world_to_camera(V, a_world)
    b_cam = world_to_camera(V, b_world)

    vis, a_cam2, b_cam2 = clip_segment_to_near(a_cam, b_cam, near)
    if not vis:
        return None

    pa = project_cam_to_screen(a_cam2, P, w, h)
    pb = project_cam_to_screen(b_cam2, P, w, h)
    if pa is None or pb is None:
        return None

    return pa, pb