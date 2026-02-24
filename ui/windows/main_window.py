# FILE: ui/windows/main_window.py
from __future__ import annotations

from typing import Any
from pathlib import Path
import numpy as np
import math

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QFileDialog

from core.geometry.vec3 import Vec3

from ui.widgets.viewport3d import Viewport3D
from ui.widgets.control_panel import ControlPanel
from ui.workers.sim_worker import SimWorker

from ui.logic.preview import compute_attack_previews
from ui.logic.pose import BodyYawFollower, compute_head_yaw_pitch

from render.scene.builder import build_scene_items
from render.scene.snapshot import SceneSnapshot, PlayerViz, BlockViz, AttackViz

from ui.assets.texture_store import TextureStore, SKIN_A_KEY, SKIN_B_KEY, BLOCK_KEY

from ui.state.app_config import AppConfig, SceneState, CameraState
from utils.config_locator import get_active_config_path, set_active_config_path
from utils.paths import config_file_path
from utils.paths import resolve_saved_path

MAX_HEAD_BODY_YAW_DEG = 75.0  # vanilla-like: head can turn relative to body up to ~75deg


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft Reach Lab (A vs B)")

        self._cfg_path = get_active_config_path()
        self.cfg = AppConfig.load_or_default(self._cfg_path)

        self.world = self.cfg.scene.to_world()

        self.textures = TextureStore()
        self.textures.load_default_block()

        self.viewport = Viewport3D(texture_resolver=self.textures.get)
        self.panel = ControlPanel()

        self._worker: SimWorker | None = None

        self._block_opacity = float(self.cfg.render.block_opacity)

        self._body_follow_a = BodyYawFollower()
        self._body_follow_b = BodyYawFollower()

        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.addWidget(self.viewport, stretch=2)
        layout.addWidget(self.panel, stretch=1)

        self._apply_config_to_ui()

        self.panel.apply_positions_clicked.connect(self._apply_positions)
        self.panel.add_block_clicked.connect(self._add_block)
        self.panel.remove_block_clicked.connect(self._remove_block)
        self.panel.remove_selected_clicked.connect(self._remove_selected_blocks)
        self.panel.start_clicked.connect(self._start_sim)
        self.panel.stop_clicked.connect(self._stop_sim)

        self.panel.apply_keybinds_clicked.connect(self._apply_settings)

        self.panel.browse_skin_a_clicked.connect(lambda: self._browse_skin("A"))
        self.panel.browse_skin_b_clicked.connect(lambda: self._browse_skin("B"))
        self.panel.reset_skin_a_clicked.connect(lambda: self._reset_skin("A"))
        self.panel.reset_skin_b_clicked.connect(lambda: self._reset_skin("B"))

        self.panel.browse_config_path_clicked.connect(self._browse_config_path)
        self.panel.use_default_config_path_clicked.connect(self._use_default_config_path)
        self.panel.save_config_now_clicked.connect(self._save_config_now)

        self._refresh_blocks_table()

        self._apply_settings()
        self._sync_view()
        self._look_at_scene_once()

    # ----- Config wiring -----
    def _apply_config_to_ui(self) -> None:
        self.panel.set_config_path(str(self._cfg_path))

        self.panel.set_positions(self.world.player_a.pos, self.world.player_b.pos)
        self.panel.set_eye_height(self.world.player_a.eye, self.world.player_b.eye)
        self.panel.set_cleanup_unused_auto(bool(self.cfg.scene.cleanup_unused_auto))

        self.panel.set_jitter(self.cfg.jitter)
        self.panel.set_sim_config(self.cfg.simulation)
        self.panel.set_block_opacity(float(self.cfg.render.block_opacity))

        self.viewport.set_keybinds(self.cfg.controls.keybinds)
        self.viewport.set_mouse_bindings(self.cfg.controls.mouse)
        self.viewport.set_control_tunings(
            mouse_sens=float(self.cfg.controls.mouse_sens),
            pan_sens=float(self.cfg.controls.pan_sens),
            move_speed=float(self.cfg.controls.move_speed),
            zoom_step=float(self.cfg.controls.zoom_step),
            wheel_factor=float(self.cfg.controls.wheel_dolly_factor),
        )

        self.panel.set_keybinds(self.cfg.controls.keybinds)
        self.panel.set_mouse_bindings(self.cfg.controls.mouse)

        cam = self.cfg.camera
        self.viewport.set_camera_state(
            pos=np.array([cam.pos[0], cam.pos[1], cam.pos[2]], dtype=np.float64),
            yaw=float(cam.yaw),
            pitch=float(cam.pitch),
            fov_y=float(np.deg2rad(cam.fov_y_deg)),
            near=float(cam.near),
            far=float(cam.far),
        )

        a_path = self.cfg.skins.resolved_a()
        b_path = self.cfg.skins.resolved_b()

        a_ok = self.textures.set_from_path(SKIN_A_KEY, a_path) if a_path is not None else False
        b_ok = self.textures.set_from_path(SKIN_B_KEY, b_path) if b_path is not None else False

        if not a_ok:
            a_ok = self.textures.load_default_skin_for(SKIN_A_KEY, self.world.player_a.model)
        if not b_ok:
            b_ok = self.textures.load_default_skin_for(SKIN_B_KEY, self.world.player_b.model)

        self.panel.set_skin_paths(self.textures.path_for(SKIN_A_KEY), self.textures.path_for(SKIN_B_KEY))
        self.panel.set_skin_status(a_ok, b_ok)

    def _capture_config_from_ui(self) -> AppConfig:
        scene = SceneState.from_world(self.world, cleanup_unused_auto=self.panel.get_cleanup_unused_auto())

        sim_cfg = self.panel.get_sim_config()
        jitter = self.panel.get_jitter()

        kb = self.panel.get_keybinds()
        mb = self.panel.get_mouse_bindings()

        cam_state = self.viewport.get_camera_state()
        cam = CameraState(
            pos=[float(cam_state["pos"][0]), float(cam_state["pos"][1]), float(cam_state["pos"][2])],  # type: ignore[index]
            yaw=float(cam_state["yaw"]),      # type: ignore[arg-type]
            pitch=float(cam_state["pitch"]),  # type: ignore[arg-type]
            fov_y_deg=float(math.degrees(float(cam_state["fov_y"]))),  # type: ignore[arg-type]
            near=float(cam_state["near"]),    # type: ignore[arg-type]
            far=float(cam_state["far"]),      # type: ignore[arg-type]
        )

        cfg = AppConfig(
            version=int(self.cfg.version),
            scene=scene,
            simulation=sim_cfg,
            jitter=jitter,
            controls=self.cfg.controls.__class__(
                keybinds=kb,
                mouse=mb,
                mouse_sens=float(self.cfg.controls.mouse_sens),
                pan_sens=float(self.cfg.controls.pan_sens),
                move_speed=float(self.cfg.controls.move_speed),
                zoom_step=float(self.cfg.controls.zoom_step),
                wheel_dolly_factor=float(self.cfg.controls.wheel_dolly_factor),
            ),
            render=self.cfg.render.__class__(block_opacity=float(self.panel.get_block_opacity())),
            skins=self.cfg.skins,
            camera=cam,
        )

        cfg.skins.set_a(resolve_saved_path(self.textures.path_for(SKIN_A_KEY)))
        cfg.skins.set_b(resolve_saved_path(self.textures.path_for(SKIN_B_KEY)))
        return cfg

    def _save_config_now(self) -> None:
        self.cfg = self._capture_config_from_ui()
        self.cfg.save(self._cfg_path)
        set_active_config_path(self._cfg_path)
        self.panel.set_config_path(str(self._cfg_path))

    def closeEvent(self, e) -> None:
        try:
            self._save_config_now()
        except Exception:
            pass
        super().closeEvent(e)

    # ----- Config path controls -----
    def _browse_config_path(self) -> None:
        start_dir = str(Path(self._cfg_path).parent if self._cfg_path else Path.home())
        default_name = str(self._cfg_path) if self._cfg_path else str(config_file_path())

        fn, _ = QFileDialog.getSaveFileName(
            self,
            "Select config.json save path",
            default_name if default_name else start_dir,
            "JSON Files (*.json)"
        )
        if not fn:
            return

        p = Path(fn)
        if p.suffix.lower() != ".json":
            p = p.with_suffix(".json")

        self._cfg_path = p
        set_active_config_path(self._cfg_path)
        self.panel.set_config_path(str(self._cfg_path))

        self._save_config_now()

    def _use_default_config_path(self) -> None:
        self._cfg_path = config_file_path()
        set_active_config_path(self._cfg_path)
        self.panel.set_config_path(str(self._cfg_path))
        self._save_config_now()

    # ----- Skin browsing -----
    def _browse_skin(self, who: str) -> None:
        start_dir = str(Path.home())
        fn, _ = QFileDialog.getOpenFileName(
            self,
            f"Select skin PNG for Player {who}",
            start_dir,
            "PNG Images (*.png)"
        )
        if not fn:
            return
        p = Path(fn)

        if who == "A":
            self.textures.set_from_path(SKIN_A_KEY, p)
        else:
            self.textures.set_from_path(SKIN_B_KEY, p)

        self.panel.set_skin_paths(self.textures.path_for(SKIN_A_KEY), self.textures.path_for(SKIN_B_KEY))
        self.panel.set_skin_status(self.textures.get(SKIN_A_KEY) is not None, self.textures.get(SKIN_B_KEY) is not None)
        self._sync_view()

    def _reset_skin(self, who: str) -> None:
        if who == "A":
            self.textures.load_default_skin_for(SKIN_A_KEY, self.world.player_a.model)
        else:
            self.textures.load_default_skin_for(SKIN_B_KEY, self.world.player_b.model)

        self.panel.set_skin_paths(self.textures.path_for(SKIN_A_KEY), self.textures.path_for(SKIN_B_KEY))
        self.panel.set_skin_status(self.textures.get(SKIN_A_KEY) is not None, self.textures.get(SKIN_B_KEY) is not None)
        self._sync_view()

    # ----- Settings apply -----
    def _apply_settings(self) -> None:
        kb = self.panel.get_keybinds()
        mb = self.panel.get_mouse_bindings()
        self._block_opacity = float(self.panel.get_block_opacity())

        self.viewport.set_keybinds(kb)
        self.viewport.set_mouse_bindings(mb)

        self._sync_view()
        self.viewport.update()

    def _reset_pose_state(self) -> None:
        self._body_follow_a.reset()
        self._body_follow_b.reset()

    # ----- Scene ops -----
    def _apply_positions(self) -> None:
        a, b = self.panel.get_positions()
        self.world.set_player_pos("A", a)
        self.world.set_player_pos("B", b)

        if self.panel.get_cleanup_unused_auto():
            self.world.cleanup_unused_auto_supports()

        self._reset_pose_state()
        self._refresh_blocks_table()
        self._sync_view()

    def _add_block(self) -> None:
        x, y, z = self.panel.get_block_coord()
        self.world.add_block(x, y, z, manual=True)
        self._refresh_blocks_table()
        self._sync_view()

    def _remove_block(self) -> None:
        x, y, z = self.panel.get_block_coord()
        self.world.remove_block(x, y, z)
        self._refresh_blocks_table()
        self._sync_view()

    def _remove_selected_blocks(self) -> None:
        model = self.panel.block_table.selectionModel()
        rows = model.selectedRows() if model is not None else []
        if not rows:
            return

        coords: list[tuple[int, int, int]] = []
        for idx in rows:
            r = idx.row()
            ix = self.panel.block_table.item(r, 0)
            iy = self.panel.block_table.item(r, 1)
            iz = self.panel.block_table.item(r, 2)
            if ix is None or iy is None or iz is None:
                continue
            coords.append((int(ix.text()), int(iy.text()), int(iz.text())))

        for x, y, z in coords:
            self.world.remove_block(x, y, z)

        self._refresh_blocks_table()
        self._sync_view()

    def _refresh_blocks_table(self) -> None:
        items = sorted(self.world.blocks.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2]))
        rows: list[tuple[int, int, int, str]] = []
        for (x, y, z), b in items:
            rows.append((x, y, z, "manual" if b.manual else "auto"))
        self.panel.set_blocks(rows)

    # ----- Simulation -----
    def _start_sim(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        self._apply_positions()

        self.panel.reset_results()
        self.panel.set_progress(0, "starting")
        self.panel.set_running(True)

        snapshot = self.world.clone()
        jitter = self.panel.get_jitter()
        cfg = self.panel.get_sim_config()

        self._worker = SimWorker(snapshot, jitter, cfg)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_payload.connect(self._on_finished)
        self._worker.start()

    def _stop_sim(self) -> None:
        if self._worker is None:
            return
        self.panel.set_progress(self.panel.progress.value(), "stopping")
        self._worker.stop()

    def _on_progress(self, percent: int, text: str) -> None:
        self.panel.set_progress(percent, text)

    def _on_finished(self, payload: Any) -> None:
        stats_ab, stats_ba, res_ab, res_ba = payload

        self.panel.show_results(stats_ab, stats_ba)
        self.panel.plot_hist(res_ab, res_ba)

        self.panel.set_running(False)
        self.panel.set_progress(100, "done")

        self._worker = None
        self._sync_view()

    # ----- View sync -----
    def _look_at_scene_once(self) -> None:
        pts = [
            np.array([self.world.player_a.pos.x, self.world.player_a.pos.y + 1.0, self.world.player_a.pos.z], dtype=np.float64),
            np.array([self.world.player_b.pos.x, self.world.player_b.pos.y + 1.0, self.world.player_b.pos.z], dtype=np.float64),
        ]
        for (x, y, z) in self.world.blocks.keys():
            pts.append(np.array([x + 0.5, y + 0.5, z + 0.5], dtype=np.float64))
        c = np.mean(np.stack(pts, axis=0), axis=0) if pts else np.array([0.0, 1.0, 0.0], dtype=np.float64)
        self.viewport.look_at(c)

    def _sync_view(self) -> None:
        reach, surf_n, att_n, attack_offset = self.panel.get_preview_params()

        ev_a, ev_b = compute_attack_previews(
            world=self.world,
            reach=float(reach),
            surface_samples=int(surf_n),
            attack_samples=int(att_n),
            attack_offset=float(attack_offset),
        )

        a_eye = self.world.player_a.eye_point()
        b_eye = self.world.player_b.eye_point()

        yaw_a_head, pitch_a_head = compute_head_yaw_pitch(a_eye, ev_a.aim_target)
        yaw_b_head, pitch_b_head = compute_head_yaw_pitch(b_eye, ev_b.aim_target)

        self._body_follow_a.ensure_initialized(self.world.player_a.pos, self.world.player_b.pos)
        self._body_follow_b.ensure_initialized(self.world.player_b.pos, self.world.player_a.pos)

        yaw_a_body = self._body_follow_a.update(yaw_a_head, max_head_body_yaw_deg=MAX_HEAD_BODY_YAW_DEG)
        yaw_b_body = self._body_follow_b.update(yaw_b_head, max_head_body_yaw_deg=MAX_HEAD_BODY_YAW_DEG)

        blocks_viz: list[BlockViz] = []
        for (x, y, z), b in self.world.blocks.items():
            blocks_viz.append(BlockViz(x=int(x), y=int(y), z=int(z), aabb=b.aabb(), manual=bool(b.manual)))

        pa = self.world.player_a
        pb = self.world.player_b

        snap = SceneSnapshot(
            player_a=PlayerViz(
                name=str(pa.name),
                foot=Vec3(pa.pos.x, pa.pos.y, pa.pos.z),
                eye=pa.eye_point(),
                hitbox=pa.aabb(),
                model=str(pa.model),
            ),
            player_b=PlayerViz(
                name=str(pb.name),
                foot=Vec3(pb.pos.x, pb.pos.y, pb.pos.z),
                eye=pb.eye_point(),
                hitbox=pb.aabb(),
                model=str(pb.model),
            ),
            blocks=blocks_viz,
            ground_y=float(self.world.ground_y),
        )

        atk_a = AttackViz(
            seg_start=ev_a.seg_start,
            seg_end=ev_a.seg_end,
            aim_target=ev_a.aim_target,
            any_reachable=bool(ev_a.any_reachable),
        )
        atk_b = AttackViz(
            seg_start=ev_b.seg_start,
            seg_end=ev_b.seg_end,
            aim_target=ev_b.aim_target,
            any_reachable=bool(ev_b.any_reachable),
        )

        items = build_scene_items(
            snapshot=snap,
            attack_a=atk_a,
            attack_b=atk_b,
            skin_a_key=SKIN_A_KEY,
            skin_b_key=SKIN_B_KEY,
            block_key=BLOCK_KEY,
            block_opacity=float(self._block_opacity),
            pose_a=(yaw_a_head, pitch_a_head, yaw_a_body),
            pose_b=(yaw_b_head, pitch_b_head, yaw_b_body),
        )

        self.viewport.set_scene(items)


def run_app() -> None:
    app = QApplication([])
    w = MainWindow()
    w.resize(1450, 820)
    w.show()
    app.exec()