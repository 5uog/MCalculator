# FILE: render/viz/builder.py
from __future__ import annotations

import numpy as np

from core.geometry.aabb import AABB
from core.geometry.vec3 import Vec3

from render.viz.items import RenderItem
from render.viz.snapshot import SceneSnapshot, AttackViz

from render.humanoid.model import (
    humanoid_parts_at,
    face_vertices_rotated,
    inflate_aabb,
    FACE_NORMAL,
    rotate_yaw_pitch_vec,
    head_neck_pivot,
    PX,
    face_vertices,
    FACES,
)
from render.humanoid.skin_uv import get_base_uv, get_overlay_uv

from utils.numeric import clamp01, finite_or

def _add_textured_part(
    items: list[RenderItem],
    part_name: str,
    box: AABB,
    texture_key: str,
    slim_arms: bool,
    overlay: bool,
    yaw: float,
    pitch: float,
    origin: Vec3,
) -> None:
    src_getter = get_overlay_uv if overlay else get_base_uv
    box2 = inflate_aabb(box, eps=PX * (0.35 if overlay else 0.0))

    for face in FACES:
        uv = src_getter(part_name, face, slim_arms)  # type: ignore[arg-type]
        if uv is None:
            continue

        v0, v1, v2, v3 = face_vertices_rotated(box2, face, yaw, pitch, origin)
        verts = np.array(
            [[v0.x, v0.y, v0.z], [v1.x, v1.y, v1.z], [v2.x, v2.y, v2.z], [v3.x, v3.y, v3.z]],
            dtype=np.float64,
        )

        n0 = FACE_NORMAL[face]
        n = rotate_yaw_pitch_vec(n0, yaw, pitch)

        items.append(
            RenderItem(
                kind="tex_quad",
                color=(255, 255, 255),
                opacity=1.0,
                verts=verts,
                texture_key=str(texture_key),
                src_rect=(float(uv.x1), float(uv.y1), float(uv.w), float(uv.h)),
                normal=n,
            )
        )

def _add_textured_block(items: list[RenderItem], block_box: AABB, texture_key: str, opacity: float) -> None:
    box2 = inflate_aabb(block_box, eps=1e-4)
    op = clamp01(finite_or(opacity, 1.0))

    for face in FACES:
        v0, v1, v2, v3 = face_vertices(box2, face)
        verts = np.array(
            [[v0.x, v0.y, v0.z], [v1.x, v1.y, v1.z], [v2.x, v2.y, v2.z], [v3.x, v3.y, v3.z]],
            dtype=np.float64,
        )
        n = FACE_NORMAL[face]

        items.append(
            RenderItem(
                kind="tex_quad",
                color=(255, 255, 255),
                opacity=float(op),
                verts=verts,
                texture_key=str(texture_key),
                src_rect=None,  # full texture
                normal=n,
            )
        )

def build_scene_items(
    snapshot: SceneSnapshot,
    attack_a: AttackViz,
    attack_b: AttackViz,
    skin_a_key: str,
    skin_b_key: str,
    block_key: str,
    block_opacity: float,
    pose_a: tuple[float, float, float],  # (yaw_head, pitch_head, yaw_body)
    pose_b: tuple[float, float, float],  # (yaw_head, pitch_head, yaw_body)
) -> list[RenderItem]:
    """
    Build a Qt-agnostic list of RenderItems for the viewport.
    This module is presentation-only and does not depend on the domain World type.
    """
    items: list[RenderItem] = []

    for b in sorted(snapshot.blocks, key=lambda bb: (bb.y, bb.x, bb.z)):
        _add_textured_block(items, b.aabb, block_key, block_opacity)
        label = f"Block\n({b.x},{b.y},{b.z})"
        col = (170, 170, 170) if b.manual else (120, 120, 120)
        items.append(RenderItem(kind="aabb", aabb=b.aabb, color=col, label=label))

    items.append(RenderItem(kind="aabb", aabb=snapshot.player_a.hitbox, color=(0, 140, 255), label="Player A hitbox"))
    items.append(RenderItem(kind="aabb", aabb=snapshot.player_b.hitbox, color=(255, 70, 70), label="Player B hitbox"))

    slim_a = str(snapshot.player_a.model).strip().lower() == "alex"
    slim_b = str(snapshot.player_b.model).strip().lower() == "alex"

    parts_a = humanoid_parts_at(snapshot.player_a.foot, slim_arms=slim_a)
    parts_b = humanoid_parts_at(snapshot.player_b.foot, slim_arms=slim_b)

    a_neck = head_neck_pivot(parts_a["head"].box)
    b_neck = head_neck_pivot(parts_b["head"].box)

    yaw_a_head, pitch_a_head, yaw_a_body = pose_a
    yaw_b_head, pitch_b_head, yaw_b_body = pose_b

    for pn, part in parts_a.items():
        if pn == "head":
            _add_textured_part(items, pn, part.box, skin_a_key, slim_a, False, yaw_a_head, pitch_a_head, a_neck)
        else:
            _add_textured_part(items, pn, part.box, skin_a_key, slim_a, False, yaw_a_body, 0.0, snapshot.player_a.foot)

    for pn, part in parts_b.items():
        if pn == "head":
            _add_textured_part(items, pn, part.box, skin_b_key, slim_b, False, yaw_b_head, pitch_b_head, b_neck)
        else:
            _add_textured_part(items, pn, part.box, skin_b_key, slim_b, False, yaw_b_body, 0.0, snapshot.player_b.foot)

    for pn, part in parts_a.items():
        if pn == "head":
            _add_textured_part(items, pn, part.box, skin_a_key, slim_a, True, yaw_a_head, pitch_a_head, a_neck)
        else:
            _add_textured_part(items, pn, part.box, skin_a_key, slim_a, True, yaw_a_body, 0.0, snapshot.player_a.foot)

    for pn, part in parts_b.items():
        if pn == "head":
            _add_textured_part(items, pn, part.box, skin_b_key, slim_b, True, yaw_b_head, pitch_b_head, b_neck)
        else:
            _add_textured_part(items, pn, part.box, skin_b_key, slim_b, True, yaw_b_body, 0.0, snapshot.player_b.foot)

    items.append(
        RenderItem(
            kind="segment",
            color=(0, 140, 255),
            a=np.array([attack_a.seg_start.x, attack_a.seg_start.y, attack_a.seg_start.z], dtype=np.float64),
            b=np.array([attack_a.seg_end.x, attack_a.seg_end.y, attack_a.seg_end.z], dtype=np.float64),
        )
    )
    items.append(
        RenderItem(
            kind="segment",
            color=(255, 70, 70),
            a=np.array([attack_b.seg_start.x, attack_b.seg_start.y, attack_b.seg_start.z], dtype=np.float64),
            b=np.array([attack_b.seg_end.x, attack_b.seg_end.y, attack_b.seg_end.z], dtype=np.float64),
        )
    )

    a_eye = snapshot.player_a.eye
    b_eye = snapshot.player_b.eye
    a_aim = np.array([attack_a.aim_target.x, attack_a.aim_target.y, attack_a.aim_target.z], dtype=np.float64)
    b_aim = np.array([attack_b.aim_target.x, attack_b.aim_target.y, attack_b.aim_target.z], dtype=np.float64)

    items.append(
        RenderItem(
            kind="segment",
            color=(220, 220, 220),
            a=np.array([a_eye.x, a_eye.y, a_eye.z], dtype=np.float64),
            b=a_aim,
        )
    )
    items.append(
        RenderItem(
            kind="segment",
            color=(220, 220, 220),
            a=np.array([b_eye.x, b_eye.y, b_eye.z], dtype=np.float64),
            b=b_aim,
        )
    )

    if not bool(attack_a.any_reachable):
        mid = (np.array([a_eye.x, a_eye.y, a_eye.z], dtype=np.float64) + a_aim) * 0.5
        items.append(RenderItem(kind="cross", color=(0, 140, 255), p=mid, size_px=12))
    if not bool(attack_b.any_reachable):
        mid = (np.array([b_eye.x, b_eye.y, b_eye.z], dtype=np.float64) + b_aim) * 0.5
        items.append(RenderItem(kind="cross", color=(255, 70, 70), p=mid, size_px=12))

    return items