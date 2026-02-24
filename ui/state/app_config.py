# FILE: ui/state/app_config.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import math

from core.geometry.vec3 import Vec3
from scene.world import World
from scene.entities import Player, Block, STEVE_GEOMETRY, ALEX_GEOMETRY
from sim.config import SimConfig
from sim.jitter import JitterSpec
from app.config_store import load_json, save_json_atomic
from app.paths import config_file_path, normalize_saved_path, resolve_saved_path

from ui.state.default_controls import DEFAULT_KEYBINDS, DEFAULT_MOUSE
from utils.numeric import clampf_finite, clampi

def _f(d: dict[str, Any], k: str, default: Any) -> Any:
    v = d.get(k, default)
    return v if v is not None else default

def _vec3_from(d: Any, default: Vec3) -> Vec3:
    if not isinstance(d, dict):
        return default
    return Vec3(
        float(_f(d, "x", default.x)),
        float(_f(d, "y", default.y)),
        float(_f(d, "z", default.z)),
    )

def _vec3_to(v: Vec3) -> dict[str, float]:
    return {"x": float(v.x), "y": float(v.y), "z": float(v.z)}

@dataclass
class SceneState:
    a_pos: Vec3 = Vec3(3.5, 0.0, 1.5)
    b_pos: Vec3 = Vec3(1.5, 2.0, 3.5)

    a_model: str = "Steve"
    b_model: str = "Alex"

    a_width: float = 0.6
    a_height: float = 1.8
    a_eye: float = 1.62

    b_width: float = 0.6
    b_height: float = 1.8
    b_eye: float = 1.62

    ground_y: int = 0
    cleanup_unused_auto: bool = True

    manual_blocks: list[tuple[int, int, int]] = field(default_factory=list)

    def to_world(self) -> World:
        a_geo = ALEX_GEOMETRY if str(self.a_model).strip().lower() == "alex" else STEVE_GEOMETRY
        b_geo = ALEX_GEOMETRY if str(self.b_model).strip().lower() == "alex" else STEVE_GEOMETRY

        a = Player(
            name="A",
            pos=Vec3(self.a_pos.x, self.a_pos.y, self.a_pos.z),
            width=float(self.a_width),
            height=float(self.a_height),
            eye=float(self.a_eye),
            model=str(self.a_model),
            geometry=a_geo,
        )
        b = Player(
            name="B",
            pos=Vec3(self.b_pos.x, self.b_pos.y, self.b_pos.z),
            width=float(self.b_width),
            height=float(self.b_height),
            eye=float(self.b_eye),
            model=str(self.b_model),
            geometry=b_geo,
        )

        w = World(a, b, ground_y=int(self.ground_y))
        for (x, y, z) in self.manual_blocks:
            key = (int(x), int(y), int(z))
            w.blocks[key] = Block(key[0], key[1], key[2], manual=True)

        w.rebuild_supports()
        return w

    @staticmethod
    def from_world(world: World, cleanup_unused_auto: bool) -> "SceneState":
        manual = [(x, y, z) for (x, y, z), b in world.blocks.items() if bool(b.manual)]
        return SceneState(
            a_pos=Vec3(world.player_a.pos.x, world.player_a.pos.y, world.player_a.pos.z),
            b_pos=Vec3(world.player_b.pos.x, world.player_b.pos.y, world.player_b.pos.z),
            a_model=str(world.player_a.model),
            b_model=str(world.player_b.model),
            a_width=float(world.player_a.width),
            a_height=float(world.player_a.height),
            a_eye=float(world.player_a.eye),
            b_width=float(world.player_b.width),
            b_height=float(world.player_b.height),
            b_eye=float(world.player_b.eye),
            ground_y=int(world.ground_y),
            cleanup_unused_auto=bool(cleanup_unused_auto),
            manual_blocks=list(manual),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "a_pos": _vec3_to(self.a_pos),
            "b_pos": _vec3_to(self.b_pos),
            "a_model": str(self.a_model),
            "b_model": str(self.b_model),
            "a_width": float(self.a_width),
            "a_height": float(self.a_height),
            "a_eye": float(self.a_eye),
            "b_width": float(self.b_width),
            "b_height": float(self.b_height),
            "b_eye": float(self.b_eye),
            "ground_y": int(self.ground_y),
            "cleanup_unused_auto": bool(self.cleanup_unused_auto),
            "manual_blocks": [[int(x), int(y), int(z)] for (x, y, z) in self.manual_blocks],
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "SceneState":
        a_pos = _vec3_from(_f(d, "a_pos", {}), Vec3(3.5, 0.0, 1.5))
        b_pos = _vec3_from(_f(d, "b_pos", {}), Vec3(1.5, 2.0, 3.5))

        mb_raw = _f(d, "manual_blocks", [])
        blocks: list[tuple[int, int, int]] = []
        if isinstance(mb_raw, list):
            for row in mb_raw:
                if isinstance(row, (list, tuple)) and len(row) == 3:
                    blocks.append((int(row[0]), int(row[1]), int(row[2])))

        return SceneState(
            a_pos=a_pos,
            b_pos=b_pos,
            a_model=str(_f(d, "a_model", "Steve")),
            b_model=str(_f(d, "b_model", "Alex")),
            a_width=clampf_finite(_f(d, "a_width", 0.6), 0.01, 10.0, 0.6),
            a_height=clampf_finite(_f(d, "a_height", 1.8), 0.01, 10.0, 1.8),
            a_eye=clampf_finite(_f(d, "a_eye", 1.62), 0.0, 10.0, 1.62),
            b_width=clampf_finite(_f(d, "b_width", 0.6), 0.01, 10.0, 0.6),
            b_height=clampf_finite(_f(d, "b_height", 1.8), 0.01, 10.0, 1.8),
            b_eye=clampf_finite(_f(d, "b_eye", 1.62), 0.0, 10.0, 1.62),
            ground_y=clampi(_f(d, "ground_y", 0), -9999, 9999, 0),
            cleanup_unused_auto=bool(_f(d, "cleanup_unused_auto", True)),
            manual_blocks=blocks,
        )

@dataclass
class CameraState:
    pos: list[float] = field(default_factory=lambda: [8.0, 6.0, 12.0])
    yaw: float = float(np.deg2rad(-135.0))
    pitch: float = float(np.deg2rad(-25.0))
    fov_y_deg: float = 60.0
    near: float = 0.1
    far: float = 200.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pos": [float(self.pos[0]), float(self.pos[1]), float(self.pos[2])],
            "yaw": float(self.yaw),
            "pitch": float(self.pitch),
            "fov_y_deg": float(self.fov_y_deg),
            "near": float(self.near),
            "far": float(self.far),
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "CameraState":
        p = _f(d, "pos", [8.0, 6.0, 12.0])
        pos = [8.0, 6.0, 12.0]
        if isinstance(p, list) and len(p) == 3:
            try:
                pos = [float(p[0]), float(p[1]), float(p[2])]
            except Exception:
                pos = [8.0, 6.0, 12.0]

        yaw = clampf_finite(_f(d, "yaw", float(np.deg2rad(-135.0))), -1e9, 1e9, float(np.deg2rad(-135.0)))
        pitch = clampf_finite(_f(d, "pitch", float(np.deg2rad(-25.0))), -1e9, 1e9, float(np.deg2rad(-25.0)))

        return CameraState(
            pos=pos,
            yaw=float(yaw),
            pitch=float(pitch),
            fov_y_deg=clampf_finite(_f(d, "fov_y_deg", 60.0), 1.0, 179.0, 60.0),
            near=clampf_finite(_f(d, "near", 0.1), 1e-4, 100.0, 0.1),
            far=clampf_finite(_f(d, "far", 200.0), 1.0, 1e6, 200.0),
        )

@dataclass
class ControlState:
    keybinds: dict[str, int] = field(default_factory=dict)
    mouse: dict[str, int] = field(default_factory=dict)

    mouse_sens: float = 0.005
    pan_sens: float = 0.012
    move_speed: float = 0.45
    zoom_step: float = 0.24
    wheel_dolly_factor: float = 0.002

    def __post_init__(self) -> None:
        # Normal path: fill missing keys only, never overwrite existing values (including 0).
        self.ensure_defaults(migrate_blankish=False)

    @staticmethod
    def _blankish(d: dict[str, int]) -> bool:
        if not d:
            return True
        vals = [int(v) for v in d.values() if v is not None]
        if not vals:
            return True
        return all(v == 0 for v in vals)

    def ensure_defaults(self, migrate_blankish: bool) -> None:
        """
        - migrate_blankish=False:
            Fill missing keys only (do not overwrite).
        - migrate_blankish=True:
            If the whole set is blank/zero, initialize to defaults once.
            Otherwise behave like migrate_blankish=False.
        """
        if migrate_blankish and self._blankish(self.keybinds):
            self.keybinds.clear()
            self.keybinds.update({k: int(v) for (k, v) in DEFAULT_KEYBINDS.items()})
        else:
            for k, v in DEFAULT_KEYBINDS.items():
                if k not in self.keybinds:
                    self.keybinds[k] = int(v)

        if migrate_blankish and self._blankish(self.mouse):
            self.mouse.clear()
            self.mouse.update({k: int(v) for (k, v) in DEFAULT_MOUSE.items()})
        else:
            for k, v in DEFAULT_MOUSE.items():
                if k not in self.mouse:
                    self.mouse[k] = int(v)

    def to_dict(self) -> dict[str, Any]:
        return {
            "keybinds": {str(k): int(v) for (k, v) in self.keybinds.items()},
            "mouse": {str(k): int(v) for (k, v) in self.mouse.items()},
            "mouse_sens": float(self.mouse_sens),
            "pan_sens": float(self.pan_sens),
            "move_speed": float(self.move_speed),
            "zoom_step": float(self.zoom_step),
            "wheel_dolly_factor": float(self.wheel_dolly_factor),
        }

    @staticmethod
    def from_dict(d: dict[str, Any], migrate_blankish: bool) -> "ControlState":
        kb_raw = _f(d, "keybinds", {})
        ms_raw = _f(d, "mouse", {})

        kb: dict[str, int] = {}
        if isinstance(kb_raw, dict):
            for k, v in kb_raw.items():
                try:
                    kb[str(k)] = int(v)
                except Exception:
                    pass

        ms: dict[str, int] = {}
        if isinstance(ms_raw, dict):
            for k, v in ms_raw.items():
                try:
                    ms[str(k)] = int(v)
                except Exception:
                    pass

        cs = ControlState(
            keybinds=kb,
            mouse=ms,
            mouse_sens=clampf_finite(_f(d, "mouse_sens", 0.005), 1e-6, 1.0, 0.005),
            pan_sens=clampf_finite(_f(d, "pan_sens", 0.012), 1e-6, 10.0, 0.012),
            move_speed=clampf_finite(_f(d, "move_speed", 0.45), 1e-6, 100.0, 0.45),
            zoom_step=clampf_finite(_f(d, "zoom_step", 0.24), 1e-6, 100.0, 0.24),
            wheel_dolly_factor=clampf_finite(_f(d, "wheel_dolly_factor", 0.002), 1e-6, 1.0, 0.002),
        )
        # One-time initialization only when the whole set is blank/zero.
        cs.ensure_defaults(migrate_blankish=bool(migrate_blankish))
        return cs

@dataclass
class RenderState:
    block_opacity: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"block_opacity": float(self.block_opacity)}

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "RenderState":
        return RenderState(block_opacity=clampf_finite(_f(d, "block_opacity", 1.0), 0.0, 1.0, 1.0))

@dataclass
class SkinState:
    path_a: str = ""
    path_b: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"path_a": str(self.path_a), "path_b": str(self.path_b)}

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "SkinState":
        return SkinState(
            path_a=str(_f(d, "path_a", "")),
            path_b=str(_f(d, "path_b", "")),
        )

    def resolved_a(self) -> Path | None:
        return resolve_saved_path(self.path_a)

    def resolved_b(self) -> Path | None:
        return resolve_saved_path(self.path_b)

    def set_a(self, p: Path | None) -> None:
        self.path_a = normalize_saved_path(p)

    def set_b(self, p: Path | None) -> None:
        self.path_b = normalize_saved_path(p)

@dataclass
class AppConfig:
    # Version 2: default-fill fix and one-time migration from blank keybinds/mouse.
    version: int = 2

    scene: SceneState = field(default_factory=SceneState)
    simulation: SimConfig = field(default_factory=SimConfig)
    jitter: JitterSpec = field(default_factory=JitterSpec)

    controls: ControlState = field(default_factory=ControlState)
    render: RenderState = field(default_factory=RenderState)
    skins: SkinState = field(default_factory=SkinState)
    camera: CameraState = field(default_factory=CameraState)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": int(self.version),
            "scene": self.scene.to_dict(),
            "simulation": {
                "reach": float(self.simulation.reach),
                "trials": int(self.simulation.trials),
                "surface_samples": int(self.simulation.surface_samples),
                "attack_offset": float(self.simulation.attack_offset),
                "attack_samples": int(self.simulation.attack_samples),
            },
            "jitter": {
                "jx": float(self.jitter.jx),
                "jy": float(self.jitter.jy),
                "jz": float(self.jitter.jz),
                "seed": int(self.jitter.seed),
            },
            "controls": self.controls.to_dict(),
            "render": self.render.to_dict(),
            "skins": self.skins.to_dict(),
            "camera": self.camera.to_dict(),
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "AppConfig":
        ver = clampi(_f(d, "version", 1), 1, 9999, 1)
        migrate_blankish = (ver < 2)

        scene = SceneState.from_dict(_f(d, "scene", {}))
        sim_d = _f(d, "simulation", {})
        if not isinstance(sim_d, dict):
            sim_d = {}

        simulation = SimConfig(
            reach=clampf_finite(_f(sim_d, "reach", 3.0), 0.0, 20.0, 3.0),
            trials=clampi(_f(sim_d, "trials", 5000), 1, 5_000_000, 5000),
            surface_samples=clampi(_f(sim_d, "surface_samples", 15), 1, 180, 15),
            attack_offset=clampf_finite(_f(sim_d, "attack_offset", 0.8), 0.0, 10.0, 0.8),
            attack_samples=clampi(_f(sim_d, "attack_samples", 9), 1, 99, 9),
        )

        jit_d = _f(d, "jitter", {})
        if not isinstance(jit_d, dict):
            jit_d = {}
        jitter = JitterSpec(
            jx=clampf_finite(_f(jit_d, "jx", 0.5), 0.0, 5.0, 0.5),
            jy=clampf_finite(_f(jit_d, "jy", 0.0), 0.0, 5.0, 0.0),
            jz=clampf_finite(_f(jit_d, "jz", 0.5), 0.0, 5.0, 0.5),
            seed=clampi(_f(jit_d, "seed", 12345), 0, 2_147_483_647, 12345),
        )

        controls_d = _f(d, "controls", {})
        render_d = _f(d, "render", {})
        skins_d = _f(d, "skins", {})
        camera_d = _f(d, "camera", {})

        controls = ControlState.from_dict(controls_d, migrate_blankish=migrate_blankish) if isinstance(controls_d, dict) else ControlState()
        render = RenderState.from_dict(render_d) if isinstance(render_d, dict) else RenderState()
        skins = SkinState.from_dict(skins_d) if isinstance(skins_d, dict) else SkinState()
        camera = CameraState.from_dict(camera_d) if isinstance(camera_d, dict) else CameraState()

        out_ver = 2 if ver < 2 else ver

        return AppConfig(
            version=int(out_ver),
            scene=scene,
            simulation=simulation,
            jitter=jitter,
            controls=controls,
            render=render,
            skins=skins,
            camera=camera,
        )

    @staticmethod
    def load_or_default(path: Path | None = None) -> "AppConfig":
        p = Path(path) if path is not None else config_file_path()
        raw = load_json(p)
        if raw is None:
            return AppConfig()
        try:
            return AppConfig.from_dict(raw)
        except Exception:
            return AppConfig()

    def save(self, path: Path | None = None) -> None:
        p = Path(path) if path is not None else config_file_path()
        save_json_atomic(p, self.to_dict())