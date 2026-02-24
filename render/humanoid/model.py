# FILE: render/humanoid/model.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple
import math
import numpy as np
from core.geometry.vec3 import Vec3
from core.geometry.aabb import AABB
from render.math.transform import rotate_model_point, rotate_model_vec

# Pixel -> world units scaling:
# Vanilla model total height is 32px (legs 12 + body 12 + head 8) = 32px
PX = 1.8 / 32.0

LEG_H = 12 * PX
BODY_H = 12 * PX
HEAD_H = 8 * PX

LEG_D = 4 * PX
BODY_W = 8 * PX
BODY_D = 4 * PX

ARM_D = 4 * PX
ARM_W_REG = 4 * PX
ARM_W_SLIM = 3 * PX

FACES = ("top", "bottom", "right", "front", "left", "back")

# Unrotated normals (forward=+Z)
FACE_NORMAL = {
    "front":  np.array([0.0, 0.0, 1.0], dtype=np.float64),
    "back":   np.array([0.0, 0.0, -1.0], dtype=np.float64),
    "right":  np.array([1.0, 0.0, 0.0], dtype=np.float64),
    "left":   np.array([-1.0, 0.0, 0.0], dtype=np.float64),
    "top":    np.array([0.0, 1.0, 0.0], dtype=np.float64),
    "bottom": np.array([0.0, -1.0, 0.0], dtype=np.float64),
}

@dataclass(frozen=True)
class Part:
    name: str
    box: AABB

def inflate_aabb(box: AABB, eps: float) -> AABB:
    return AABB(
        Vec3(box.mn.x - eps, box.mn.y - eps, box.mn.z - eps),
        Vec3(box.mx.x + eps, box.mx.y + eps, box.mx.z + eps),
    )

def aabb_center(box: AABB) -> Vec3:
    return Vec3(
        float((box.mn.x + box.mx.x) * 0.5),
        float((box.mn.y + box.mx.y) * 0.5),
        float((box.mn.z + box.mx.z) * 0.5),
    )

def head_neck_pivot(head_box: AABB) -> Vec3:
    """
    Neck pivot = bottom-center of the head box.
    This matches vanilla ModelBiped head cube design (bottom at pivot).
    """
    return Vec3(
        float((head_box.mn.x + head_box.mx.x) * 0.5),
        float(head_box.mn.y),
        float((head_box.mn.z + head_box.mx.z) * 0.5),
    )

def yaw_to_face(from_pos: Vec3, to_pos: Vec3) -> float:
    """
    forward=+Z. yaw=0 faces +Z. Positive yaw rotates toward +X.
    """
    dx = float(to_pos.x - from_pos.x)
    dz = float(to_pos.z - from_pos.z)
    if abs(dx) < 1e-12 and abs(dz) < 1e-12:
        return 0.0
    return math.atan2(dx, dz)

def pitch_to_face(from_pos: Vec3, to_pos: Vec3) -> float:
    """
    forward=+Z. Positive pitch looks upward (+Y).
    """
    dx = float(to_pos.x - from_pos.x)
    dy = float(to_pos.y - from_pos.y)
    dz = float(to_pos.z - from_pos.z)
    horiz = math.sqrt(dx*dx + dz*dz)
    if horiz < 1e-12 and abs(dy) < 1e-12:
        return 0.0
    return math.atan2(dy, horiz)

def rotate_yaw_pitch_point(p: Vec3, yaw: float, pitch: float, origin: Vec3) -> Vec3:
    return rotate_model_point(p, yaw, pitch, origin)

def rotate_yaw_pitch_vec(v: np.ndarray, yaw: float, pitch: float) -> np.ndarray:
    return rotate_model_vec(v, yaw, pitch)

def humanoid_parts_at(foot_center: Vec3, slim_arms: bool) -> Dict[str, Part]:
    """
    Visual-only humanoid geometry aligned to foot center.
    Unrotated forward: +Z.
    """
    x0 = float(foot_center.x)
    y0 = float(foot_center.y)
    z0 = float(foot_center.z)

    arm_w = ARM_W_SLIM if slim_arms else ARM_W_REG

    y_leg0, y_leg1 = y0, y0 + LEG_H
    y_body0, y_body1 = y_leg1, y_leg1 + BODY_H
    y_head0, y_head1 = y_body1, y_body1 + HEAD_H

    left_leg = AABB(
        Vec3(x0 - 4 * PX, y_leg0, z0 - LEG_D / 2.0),
        Vec3(x0 + 0 * PX, y_leg1, z0 + LEG_D / 2.0),
    )
    right_leg = AABB(
        Vec3(x0 + 0 * PX, y_leg0, z0 - LEG_D / 2.0),
        Vec3(x0 + 4 * PX, y_leg1, z0 + LEG_D / 2.0),
    )

    torso = AABB(
        Vec3(x0 - BODY_W / 2.0, y_body0, z0 - BODY_D / 2.0),
        Vec3(x0 + BODY_W / 2.0, y_body1, z0 + BODY_D / 2.0),
    )

    head = AABB(
        Vec3(x0 - 4 * PX, y_head0, z0 - 4 * PX),
        Vec3(x0 + 4 * PX, y_head1, z0 + 4 * PX),
    )

    right_arm = AABB(
        Vec3(x0 + BODY_W / 2.0, y_body0, z0 - ARM_D / 2.0),
        Vec3(x0 + BODY_W / 2.0 + arm_w, y_body1, z0 + ARM_D / 2.0),
    )
    left_arm = AABB(
        Vec3(x0 - BODY_W / 2.0 - arm_w, y_body0, z0 - ARM_D / 2.0),
        Vec3(x0 - BODY_W / 2.0, y_body1, z0 + ARM_D / 2.0),
    )

    return {
        "head": Part("head", head),
        "torso": Part("torso", torso),
        "right_arm": Part("right_arm", right_arm),
        "left_arm": Part("left_arm", left_arm),
        "right_leg": Part("right_leg", right_leg),
        "left_leg": Part("left_leg", left_leg),
    }

def face_vertices(box: AABB, face: str) -> Tuple[Vec3, Vec3, Vec3, Vec3]:
    """
    Unrotated face vertices order:
        top-left, top-right, bottom-right, bottom-left (as seen from outside).
    Unrotated forward: +Z (front face is z=mx.z).
    """
    x0, y0, z0 = box.mn.x, box.mn.y, box.mn.z
    x1, y1, z1 = box.mx.x, box.mx.y, box.mx.z

    if face == "front":
        return (Vec3(x0, y1, z1), Vec3(x1, y1, z1), Vec3(x1, y0, z1), Vec3(x0, y0, z1))
    if face == "back":
        return (Vec3(x1, y1, z0), Vec3(x0, y1, z0), Vec3(x0, y0, z0), Vec3(x1, y0, z0))
    if face == "right":
        return (Vec3(x1, y1, z0), Vec3(x1, y1, z1), Vec3(x1, y0, z1), Vec3(x1, y0, z0))
    if face == "left":
        return (Vec3(x0, y1, z1), Vec3(x0, y1, z0), Vec3(x0, y0, z0), Vec3(x0, y0, z1))
    if face == "top":
        return (Vec3(x0, y1, z0), Vec3(x1, y1, z0), Vec3(x1, y1, z1), Vec3(x0, y1, z1))
    if face == "bottom":
        return (Vec3(x0, y0, z1), Vec3(x1, y0, z1), Vec3(x1, y0, z0), Vec3(x0, y0, z0))

    raise KeyError(face)

def face_vertices_rotated(box: AABB, face: str, yaw: float, pitch: float, origin: Vec3) -> Tuple[Vec3, Vec3, Vec3, Vec3]:
    v0, v1, v2, v3 = face_vertices(box, face)
    return (
        rotate_yaw_pitch_point(v0, yaw, pitch, origin),
        rotate_yaw_pitch_point(v1, yaw, pitch, origin),
        rotate_yaw_pitch_point(v2, yaw, pitch, origin),
        rotate_yaw_pitch_point(v3, yaw, pitch, origin),
    )