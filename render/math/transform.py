# FILE: render/math/transform.py
from __future__ import annotations
import math
import numpy as np
from core.geometry.vec3 import Vec3

def rot_yaw_pitch_camera(yaw: float, pitch: float) -> np.ndarray:
    """
    Camera convention:
        - yaw around +Y
        - pitch around +X
        - forward basis = (0,0,-1) in camera local
    """
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    Ry = np.array([
        [ cy, 0.0, sy],
        [0.0, 1.0, 0.0],
        [-sy, 0.0, cy],
    ], dtype=np.float64)

    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0,  cp, -sp],
        [0.0,  sp,  cp],
    ], dtype=np.float64)

    return Ry @ Rx

def rot_yaw_pitch_model(yaw: float, pitch: float) -> np.ndarray:
    """
    Model convention (humanoid):
        - model forward = +Z
        - pitch>0 looks up (+Z toward +Y)
    """
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    Ry = np.array([
        [ cy, 0.0, sy],
        [0.0, 1.0, 0.0],
        [-sy, 0.0, cy],
    ], dtype=np.float64)

    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0,  cp,  sp],
        [0.0, -sp,  cp],
    ], dtype=np.float64)

    return Ry @ Rx

def rotate_model_point(p: Vec3, yaw: float, pitch: float, origin: Vec3) -> Vec3:
    R = rot_yaw_pitch_model(yaw, pitch)
    v = np.array([float(p.x - origin.x), float(p.y - origin.y), float(p.z - origin.z)], dtype=np.float64)
    vr = R @ v
    return Vec3(float(origin.x + vr[0]), float(origin.y + vr[1]), float(origin.z + vr[2]))

def rotate_model_vec(v: np.ndarray, yaw: float, pitch: float) -> np.ndarray:
    R = rot_yaw_pitch_model(yaw, pitch)
    vv = np.array([float(v[0]), float(v[1]), float(v[2])], dtype=np.float64)
    return (R @ vv).astype(np.float64)