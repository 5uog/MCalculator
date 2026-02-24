# FILE: ui/widgets/control_panel.py
from __future__ import annotations

import numpy as np

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QDoubleSpinBox, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QCheckBox, QLabel, QTabWidget, QScrollArea, QAbstractItemView, QHeaderView,
    QProgressBar, QLineEdit, QKeySequenceEdit, QComboBox
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.geometry.vec3 import Vec3
from sim.jitter import JitterSpec
from sim.config import SimConfig
from core.metrics.types import SummaryStats, TrialResult
from utils.qt import keyseq_to_int, enum_int
from ui.state.default_controls import DEFAULT_KEYBINDS, DEFAULT_MOUSE

class ControlPanel(QWidget):
    apply_positions_clicked = pyqtSignal()
    add_block_clicked = pyqtSignal()
    remove_block_clicked = pyqtSignal()
    remove_selected_clicked = pyqtSignal()
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    apply_keybinds_clicked = pyqtSignal()

    browse_skin_a_clicked = pyqtSignal()
    browse_skin_b_clicked = pyqtSignal()
    reset_skin_a_clicked = pyqtSignal()
    reset_skin_b_clicked = pyqtSignal()

    browse_config_path_clicked = pyqtSignal()
    use_default_config_path_clicked = pyqtSignal()
    save_config_now_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._attack_offset = 0.8

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self._build_scene_tab()
        self._build_simulation_tab()
        self._build_results_tab()
        self._build_settings_tab()

        self.set_running(False)
        self.reset_results()
        self.set_progress(0, "idle")

    # ---------- Public getters ----------
    def get_positions(self) -> tuple[Vec3, Vec3]:
        a = Vec3(float(self.ax.value()), float(self.ay.value()), float(self.az.value()))
        b = Vec3(float(self.bx.value()), float(self.by.value()), float(self.bz.value()))
        return a, b

    def get_cleanup_unused_auto(self) -> bool:
        return self.chk_cleanup.isChecked()

    def get_block_coord(self) -> tuple[int, int, int]:
        return (int(self.blx.value()), int(self.bly.value()), int(self.blz.value()))

    def get_jitter(self) -> JitterSpec:
        return JitterSpec(
            jx=float(self.jx.value()),
            jy=float(self.jy.value()),
            jz=float(self.jz.value()),
            seed=int(self.seed.value()),
        )

    def get_sim_config(self) -> SimConfig:
        return SimConfig(
            reach=float(self.reach.value()),
            trials=int(self.trials.value()),
            surface_samples=int(self.surface_samples.value()),
            attack_offset=float(self._attack_offset),
            attack_samples=int(self.attack_samples.value()),
        )

    def get_preview_params(self) -> tuple[float, int, int, float]:
        return (
            float(self.reach.value()),
            int(self.surface_samples.value()),
            int(self.attack_samples.value()),
            float(self._attack_offset),
        )

    def get_keybinds(self) -> dict[str, int]:
        return {
            "forward": keyseq_to_int(self.k_forward.keySequence()),
            "back": keyseq_to_int(self.k_back.keySequence()),
            "left": keyseq_to_int(self.k_left.keySequence()),
            "right": keyseq_to_int(self.k_right.keySequence()),
            "down": keyseq_to_int(self.k_down.keySequence()),
            "up": keyseq_to_int(self.k_up.keySequence()),
            "zoom_in": keyseq_to_int(self.k_zoom_in.keySequence()),
            "zoom_out": keyseq_to_int(self.k_zoom_out.keySequence()),
        }

    def get_mouse_bindings(self) -> dict[str, int]:
        rotate_btn = int(self.cmb_rotate_button.currentData() or 0)
        pan_btn = int(self.cmb_pan_button.currentData() or 0)
        pan_mod = int(self.cmb_pan_modifier.currentData() or 0)
        return {
            "rotate_button": rotate_btn,
            "pan_button": pan_btn,
            "pan_modifier": pan_mod,
        }

    def get_block_opacity(self) -> float:
        return float(self.block_opacity.value())

    def get_config_path(self) -> str:
        return str(self.ed_cfg_path.text()).strip()

    # ---------- Public setters ----------
    def set_positions(self, a: Vec3, b: Vec3) -> None:
        self.ax.setValue(a.x); self.ay.setValue(a.y); self.az.setValue(a.z)
        self.bx.setValue(b.x); self.by.setValue(b.y); self.bz.setValue(b.z)

    def set_cleanup_unused_auto(self, v: bool) -> None:
        self.chk_cleanup.setChecked(bool(v))

    def set_jitter(self, j: JitterSpec) -> None:
        self.jx.setValue(float(j.jx))
        self.jy.setValue(float(j.jy))
        self.jz.setValue(float(j.jz))
        self.seed.setValue(int(j.seed))

    def set_sim_config(self, cfg: SimConfig) -> None:
        self.reach.setValue(float(cfg.reach))
        self.trials.setValue(int(cfg.trials))
        self.surface_samples.setValue(int(cfg.surface_samples))
        self.attack_samples.setValue(int(cfg.attack_samples))
        self._attack_offset = float(cfg.attack_offset)
        self.lbl_attack_offset.setText(f"{self._attack_offset:.3f}")

    def set_block_opacity(self, v: float) -> None:
        self.block_opacity.setValue(float(v))

    def set_config_path(self, p: str) -> None:
        self.ed_cfg_path.setText(str(p))

    def set_eye_height(self, eye_a: float, eye_b: float | None = None) -> None:
        ea = float(eye_a)
        eb = float(eye_b) if eye_b is not None else ea
        if abs(ea - eb) < 1e-9:
            self.lbl_eye_height.setText(f"{ea:.2f}")
        else:
            self.lbl_eye_height.setText(f"A:{ea:.2f} / B:{eb:.2f}")

    def set_blocks(self, rows: list[tuple[int, int, int, str]]) -> None:
        self.block_table.setRowCount(len(rows))
        for r, (x, y, z, t) in enumerate(rows):
            self.block_table.setItem(r, 0, QTableWidgetItem(str(x)))
            self.block_table.setItem(r, 1, QTableWidgetItem(str(y)))
            self.block_table.setItem(r, 2, QTableWidgetItem(str(z)))
            self.block_table.setItem(r, 3, QTableWidgetItem(t))

    def set_running(self, running: bool) -> None:
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)

        self.btn_apply.setEnabled(not running)
        self.chk_cleanup.setEnabled(not running)

        self.btn_add_block.setEnabled(not running)
        self.btn_remove_block.setEnabled(not running)
        self.btn_remove_selected.setEnabled(not running)

        self.ax.setEnabled(not running); self.ay.setEnabled(not running); self.az.setEnabled(not running)
        self.bx.setEnabled(not running); self.by.setEnabled(not running); self.bz.setEnabled(not running)

        self.reach.setEnabled(not running)
        self.trials.setEnabled(not running)
        self.surface_samples.setEnabled(not running)
        self.attack_samples.setEnabled(not running)

        self.jx.setEnabled(not running); self.jy.setEnabled(not running); self.jz.setEnabled(not running)
        self.seed.setEnabled(not running)

        self.btn_apply_keybinds.setEnabled(not running)
        for w in (self.k_forward, self.k_back, self.k_left, self.k_right, self.k_down, self.k_up, self.k_zoom_in, self.k_zoom_out):
            w.setEnabled(not running)
        for w in (self.cmb_rotate_button, self.cmb_pan_button, self.cmb_pan_modifier, self.block_opacity):
            w.setEnabled(not running)

        self.btn_browse_skin_a.setEnabled(not running)
        self.btn_browse_skin_b.setEnabled(not running)
        self.btn_reset_skin_a.setEnabled(not running)
        self.btn_reset_skin_b.setEnabled(not running)

        self.btn_browse_cfg.setEnabled(not running)
        self.btn_default_cfg.setEnabled(not running)
        self.btn_save_cfg.setEnabled(not running)

        for b in self._reset_buttons:
            b.setEnabled(not running)

    def set_progress(self, percent: int, text: str) -> None:
        p = int(max(0, min(100, percent)))
        self.progress.setValue(p)
        self.progress_label.setText(text)

    def reset_results(self) -> None:
        self.results_table.setRowCount(0)
        self.ax_plot.clear()
        self.ax_plot.set_xlabel("min visible distance")
        self.ax_plot.set_ylabel("count")
        self.canvas.draw()

    def show_results(self, stats_ab: SummaryStats, stats_ba: SummaryStats) -> None:
        hit_ab = float(stats_ab.hit_prob_any)
        hit_ba = float(stats_ba.hit_prob_any)
        delta = hit_ab - hit_ba

        rows = [
            ("A->B hit_prob_any", f"{hit_ab:.6f}"),
            ("B->A hit_prob_any", f"{hit_ba:.6f}"),
            ("Advantage (A-B)", f"{delta:.6f}"),
            ("A->B mean_dist", f"{float(stats_ab.mean_dist):.6f}"),
            ("B->A mean_dist", f"{float(stats_ba.mean_dist):.6f}"),
            ("A->B p50_dist", f"{float(stats_ab.p50_dist):.6f}"),
            ("B->A p50_dist", f"{float(stats_ba.p50_dist):.6f}"),
            ("A->B visible_frac", f"{float(stats_ab.mean_visible_frac):.6f}"),
            ("B->A visible_frac", f"{float(stats_ba.mean_visible_frac):.6f}"),
            ("A->B occluded_frac", f"{float(stats_ab.mean_occluded_frac):.6f}"),
            ("B->A occluded_frac", f"{float(stats_ba.mean_occluded_frac):.6f}"),
            ("A->B within_reach_of_visible", f"{float(stats_ab.mean_within_reach_of_visible):.6f}"),
            ("B->A within_reach_of_visible", f"{float(stats_ba.mean_within_reach_of_visible):.6f}"),
            ("A->B within_reach_of_total", f"{float(stats_ab.mean_within_reach_of_total):.6f}"),
            ("B->A within_reach_of_total", f"{float(stats_ba.mean_within_reach_of_total):.6f}"),
            ("Trials used (A->B)", str(int(stats_ab.n))),
            ("Trials used (B->A)", str(int(stats_ba.n))),
        ]

        self.results_table.setRowCount(len(rows))
        for r, (k, v) in enumerate(rows):
            self.results_table.setItem(r, 0, QTableWidgetItem(k))
            self.results_table.setItem(r, 1, QTableWidgetItem(v))

    def plot_hist(self, res_ab: list[TrialResult], res_ba: list[TrialResult]) -> None:
        d_ab = np.array([x.min_dist for x in res_ab], dtype=np.float64) if res_ab else np.array([], dtype=np.float64)
        d_ba = np.array([x.min_dist for x in res_ba], dtype=np.float64) if res_ba else np.array([], dtype=np.float64)

        self.ax_plot.clear()
        bins = 60

        if d_ab.size > 0:
            self.ax_plot.hist(d_ab[np.isfinite(d_ab)], bins=bins, alpha=0.5, label="A->B")
        if d_ba.size > 0:
            self.ax_plot.hist(d_ba[np.isfinite(d_ba)], bins=bins, alpha=0.5, label="B->A")

        self.ax_plot.set_xlabel("min visible distance")
        self.ax_plot.set_ylabel("count")
        self.ax_plot.legend()
        self.canvas.draw()

    def set_keybinds(self, binds: dict[str, int]) -> None:
        self.k_forward.setKeySequence(QKeySequence(int(binds.get("forward", 0))))
        self.k_back.setKeySequence(QKeySequence(int(binds.get("back", 0))))
        self.k_left.setKeySequence(QKeySequence(int(binds.get("left", 0))))
        self.k_right.setKeySequence(QKeySequence(int(binds.get("right", 0))))
        self.k_down.setKeySequence(QKeySequence(int(binds.get("down", 0))))
        self.k_up.setKeySequence(QKeySequence(int(binds.get("up", 0))))
        self.k_zoom_in.setKeySequence(QKeySequence(int(binds.get("zoom_in", 0))))
        self.k_zoom_out.setKeySequence(QKeySequence(int(binds.get("zoom_out", 0))))

    def set_mouse_bindings(self, mb: dict[str, int]) -> None:
        def set_combo(cmb: QComboBox, v: int) -> None:
            i = cmb.findData(int(v))
            if i >= 0:
                cmb.setCurrentIndex(i)
        set_combo(self.cmb_rotate_button, int(mb.get("rotate_button", 0)))
        set_combo(self.cmb_pan_button, int(mb.get("pan_button", 0)))
        set_combo(self.cmb_pan_modifier, int(mb.get("pan_modifier", 0)))

    def set_skin_paths(self, path_a: str, path_b: str) -> None:
        self.ed_skin_a.setText(str(path_a))
        self.ed_skin_b.setText(str(path_b))

    def set_skin_status(self, a_ok: bool, b_ok: bool) -> None:
        self.lbl_skin_a.setText(f"Player A: {'loaded' if a_ok else 'missing'}")
        self.lbl_skin_b.setText(f"Player B: {'loaded' if b_ok else 'missing'}")

    # ---------- UI builders ----------
    def _wrap_scroll(self, content: QWidget) -> QScrollArea:
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QScrollArea.Shape.NoFrame)
        sc.setWidget(content)
        return sc

    def _build_scene_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)

        pos_box = QGroupBox("Scene: Positions (foot center)")
        pos_form = QFormLayout(pos_box)

        self.ax = QDoubleSpinBox(); self.ay = QDoubleSpinBox(); self.az = QDoubleSpinBox()
        self.bx = QDoubleSpinBox(); self.by = QDoubleSpinBox(); self.bz = QDoubleSpinBox()
        for sp in (self.ax, self.ay, self.az, self.bx, self.by, self.bz):
            sp.setRange(-9999.0, 9999.0)
            sp.setDecimals(6)
            sp.setSingleStep(0.1)

        pos_form.addRow(QLabel("A.x"), self.ax)
        pos_form.addRow(QLabel("A.y"), self.ay)
        pos_form.addRow(QLabel("A.z"), self.az)
        pos_form.addRow(QLabel("B.x"), self.bx)
        pos_form.addRow(QLabel("B.y"), self.by)
        pos_form.addRow(QLabel("B.z"), self.bz)

        self.chk_cleanup = QCheckBox("Remove unused auto support blocks on position update")
        self.chk_cleanup.setChecked(True)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.clicked.connect(self.apply_positions_clicked.emit)

        blocks_box = QGroupBox("Scene: Blocks (world obstacles)")
        blocks_layout = QVBoxLayout(blocks_box)

        self.block_table = QTableWidget(0, 4)
        self.block_table.setHorizontalHeaderLabels(["x", "y", "z", "type"])
        self.block_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.block_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.block_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.block_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.block_table.itemSelectionChanged.connect(self._on_block_selection_changed)

        blocks_layout.addWidget(self.block_table)

        coord_row = QHBoxLayout()
        self.blx = QSpinBox(); self.bly = QSpinBox(); self.blz = QSpinBox()
        for sp in (self.blx, self.bly, self.blz):
            sp.setRange(-9999, 9999)
            sp.setSingleStep(1)
        coord_row.addWidget(QLabel("x")); coord_row.addWidget(self.blx)
        coord_row.addWidget(QLabel("y")); coord_row.addWidget(self.bly)
        coord_row.addWidget(QLabel("z")); coord_row.addWidget(self.blz)
        blocks_layout.addLayout(coord_row)

        btn_row = QHBoxLayout()
        self.btn_add_block = QPushButton("Add")
        self.btn_remove_block = QPushButton("Remove")
        self.btn_remove_selected = QPushButton("Remove Selected")

        self.btn_add_block.clicked.connect(self.add_block_clicked.emit)
        self.btn_remove_block.clicked.connect(self.remove_block_clicked.emit)
        self.btn_remove_selected.clicked.connect(self.remove_selected_clicked.emit)

        btn_row.addWidget(self.btn_add_block)
        btn_row.addWidget(self.btn_remove_block)
        btn_row.addWidget(self.btn_remove_selected)
        blocks_layout.addLayout(btn_row)

        layout.addWidget(pos_box)
        layout.addWidget(self.chk_cleanup)
        layout.addWidget(self.btn_apply)
        layout.addSpacing(8)
        layout.addWidget(blocks_box)
        layout.addStretch(1)

        self.tabs.addTab(self._wrap_scroll(page), "Scene")

    def _build_simulation_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)

        sim_box = QGroupBox("Simulation")
        sim_form = QFormLayout(sim_box)

        self.reach = QDoubleSpinBox()
        self.reach.setRange(0.0, 20.0)
        self.reach.setDecimals(6)
        self.reach.setValue(3.0)

        self.trials = QSpinBox()
        self.trials.setRange(1, 5_000_000)
        self.trials.setValue(5000)

        self.surface_samples = QSpinBox()
        self.surface_samples.setRange(1, 180)
        self.surface_samples.setValue(15)

        self.attack_samples = QSpinBox()
        self.attack_samples.setRange(1, 99)
        self.attack_samples.setValue(9)

        self.lbl_eye_height = QLabel("1.62")
        self.lbl_attack_offset = QLabel(f"{self._attack_offset:.3f}")

        sim_form.addRow(QLabel("Reach"), self.reach)
        sim_form.addRow(QLabel("Eye height"), self.lbl_eye_height)
        sim_form.addRow(QLabel("Trials"), self.trials)
        sim_form.addRow(QLabel("Target surface samples"), self.surface_samples)
        sim_form.addRow(QLabel("Attack segment samples"), self.attack_samples)
        sim_form.addRow(QLabel("Attack segment length"), self.lbl_attack_offset)

        jitter_box = QGroupBox("Jitter (uniform)")
        jitter_form = QFormLayout(jitter_box)

        self.jx = QDoubleSpinBox(); self.jy = QDoubleSpinBox(); self.jz = QDoubleSpinBox()
        for sp in (self.jx, self.jy, self.jz):
            sp.setRange(0.0, 5.0)
            sp.setDecimals(6)
            sp.setSingleStep(0.05)
        self.jx.setValue(0.5)
        self.jy.setValue(0.0)
        self.jz.setValue(0.5)

        self.seed = QSpinBox()
        self.seed.setRange(0, 2_147_483_647)
        self.seed.setValue(12345)

        jitter_form.addRow(QLabel("Jitter x (±)"), self.jx)
        jitter_form.addRow(QLabel("Jitter y (±)"), self.jy)
        jitter_form.addRow(QLabel("Jitter z (±)"), self.jz)
        jitter_form.addRow(QLabel("Seed"), self.seed)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_start.clicked.connect(self.start_clicked.emit)
        self.btn_stop.clicked.connect(self.stop_clicked.emit)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)

        prog_box = QGroupBox("Progress")
        prog_layout = QVBoxLayout(prog_box)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress_label = QLabel("idle")
        self.progress_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        prog_layout.addWidget(self.progress)
        prog_layout.addWidget(self.progress_label)

        layout.addWidget(sim_box)
        layout.addWidget(jitter_box)
        layout.addLayout(btn_row)
        layout.addWidget(prog_box)
        layout.addStretch(1)

        self.tabs.addTab(self._wrap_scroll(page), "Simulation")

    def _build_results_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)

        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.results_table.horizontalHeader().setStretchLastSection(True)

        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.ax_plot = self.canvas.figure.subplots()

        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.results_table)
        layout.addSpacing(6)
        layout.addWidget(QLabel("Distance distribution (min visible distance):"))
        layout.addWidget(self.canvas)
        layout.addStretch(1)

        self.tabs.addTab(self._wrap_scroll(page), "Results")

    def _reset_keybind(self, name: str) -> None:
        code = int(DEFAULT_KEYBINDS.get(name, 0))
        seq = QKeySequence(code) if code != 0 else QKeySequence()
        if name == "forward":
            self.k_forward.setKeySequence(seq)
        elif name == "back":
            self.k_back.setKeySequence(seq)
        elif name == "left":
            self.k_left.setKeySequence(seq)
        elif name == "right":
            self.k_right.setKeySequence(seq)
        elif name == "down":
            self.k_down.setKeySequence(seq)
        elif name == "up":
            self.k_up.setKeySequence(seq)
        elif name == "zoom_in":
            self.k_zoom_in.setKeySequence(seq)
        elif name == "zoom_out":
            self.k_zoom_out.setKeySequence(seq)

    def _reset_mouse(self, name: str) -> None:
        v = int(DEFAULT_MOUSE.get(name, 0))
        if name == "rotate_button":
            i = self.cmb_rotate_button.findData(v)
            if i >= 0:
                self.cmb_rotate_button.setCurrentIndex(i)
        elif name == "pan_button":
            i = self.cmb_pan_button.findData(v)
            if i >= 0:
                self.cmb_pan_button.setCurrentIndex(i)
        elif name == "pan_modifier":
            i = self.cmb_pan_modifier.findData(v)
            if i >= 0:
                self.cmb_pan_modifier.setCurrentIndex(i)

    def _build_settings_tab(self) -> None:
        self._reset_buttons: list[QPushButton] = []

        page = QWidget()
        layout = QVBoxLayout(page)

        cfg_box = QGroupBox("Settings: Config file")
        cfg_layout = QVBoxLayout(cfg_box)

        self.ed_cfg_path = QLineEdit()
        self.ed_cfg_path.setReadOnly(True)

        cfg_btn_row = QHBoxLayout()
        self.btn_browse_cfg = QPushButton("Browse...")
        self.btn_default_cfg = QPushButton("Use Default")
        self.btn_save_cfg = QPushButton("Save Now")
        self.btn_browse_cfg.clicked.connect(self.browse_config_path_clicked.emit)
        self.btn_default_cfg.clicked.connect(self.use_default_config_path_clicked.emit)
        self.btn_save_cfg.clicked.connect(self.save_config_now_clicked.emit)

        cfg_btn_row.addWidget(self.btn_browse_cfg)
        cfg_btn_row.addWidget(self.btn_default_cfg)
        cfg_btn_row.addWidget(self.btn_save_cfg)

        cfg_layout.addWidget(QLabel("Active config.json path"))
        cfg_layout.addWidget(self.ed_cfg_path)
        cfg_layout.addLayout(cfg_btn_row)

        key_box = QGroupBox("Settings: Keybinds")
        key_form = QFormLayout(key_box)

        self.k_forward = QKeySequenceEdit()
        self.k_back = QKeySequenceEdit()
        self.k_left = QKeySequenceEdit()
        self.k_right = QKeySequenceEdit()
        self.k_down = QKeySequenceEdit()
        self.k_up = QKeySequenceEdit()
        self.k_zoom_in = QKeySequenceEdit()
        self.k_zoom_out = QKeySequenceEdit()

        def row_with_reset(widget: QWidget, reset_cb) -> QWidget:
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.addWidget(widget, stretch=1)
            btn = QPushButton("Reset")
            btn.clicked.connect(reset_cb)
            h.addWidget(btn)
            self._reset_buttons.append(btn)
            return w

        key_form.addRow(QLabel("Move forward"), row_with_reset(self.k_forward, lambda: self._reset_keybind("forward")))
        key_form.addRow(QLabel("Move back"), row_with_reset(self.k_back, lambda: self._reset_keybind("back")))
        key_form.addRow(QLabel("Move left"), row_with_reset(self.k_left, lambda: self._reset_keybind("left")))
        key_form.addRow(QLabel("Move right"), row_with_reset(self.k_right, lambda: self._reset_keybind("right")))
        key_form.addRow(QLabel("Move down"), row_with_reset(self.k_down, lambda: self._reset_keybind("down")))
        key_form.addRow(QLabel("Move up"), row_with_reset(self.k_up, lambda: self._reset_keybind("up")))
        key_form.addRow(QLabel("Zoom in (keyboard dolly)"), row_with_reset(self.k_zoom_in, lambda: self._reset_keybind("zoom_in")))
        key_form.addRow(QLabel("Zoom out (keyboard dolly)"), row_with_reset(self.k_zoom_out, lambda: self._reset_keybind("zoom_out")))

        mouse_box = QGroupBox("Settings: Mouse controls")
        mouse_form = QFormLayout(mouse_box)

        self.cmb_rotate_button = QComboBox()
        self.cmb_pan_button = QComboBox()
        self.cmb_pan_modifier = QComboBox()

        btn_items = [
            ("Left Button", enum_int(Qt.MouseButton.LeftButton)),
            ("Middle Button", enum_int(Qt.MouseButton.MiddleButton)),
            ("Right Button", enum_int(Qt.MouseButton.RightButton)),
        ]
        for txt, val in btn_items:
            self.cmb_rotate_button.addItem(txt, int(val))
            self.cmb_pan_button.addItem(txt, int(val))

        mod_items = [
            ("None", 0),
            ("Ctrl", enum_int(Qt.KeyboardModifier.ControlModifier)),
            ("Shift", enum_int(Qt.KeyboardModifier.ShiftModifier)),
            ("Alt", enum_int(Qt.KeyboardModifier.AltModifier)),
            ("Meta", enum_int(Qt.KeyboardModifier.MetaModifier)),
        ]
        for txt, val in mod_items:
            self.cmb_pan_modifier.addItem(txt, int(val))

        mouse_form.addRow(QLabel("Rotate (drag) button"), row_with_reset(self.cmb_rotate_button, lambda: self._reset_mouse("rotate_button")))
        mouse_form.addRow(QLabel("Pan (drag) button"), row_with_reset(self.cmb_pan_button, lambda: self._reset_mouse("pan_button")))
        mouse_form.addRow(QLabel("Pan modifier"), row_with_reset(self.cmb_pan_modifier, lambda: self._reset_mouse("pan_modifier")))

        blocks_box = QGroupBox("Settings: Block texture")
        blocks_form = QFormLayout(blocks_box)

        self.block_opacity = QDoubleSpinBox()
        self.block_opacity.setRange(0.0, 1.0)
        self.block_opacity.setDecimals(3)
        self.block_opacity.setSingleStep(0.05)
        self.block_opacity.setValue(1.0)
        blocks_form.addRow(QLabel("Opacity (0..1)"), self.block_opacity)

        self.btn_apply_keybinds = QPushButton("Apply Settings")
        self.btn_apply_keybinds.clicked.connect(self.apply_keybinds_clicked.emit)

        skin_box = QGroupBox("Settings: Player Skins (PNG)")
        skin_layout = QVBoxLayout(skin_box)

        self.lbl_skin_a = QLabel("Player A: missing")
        self.lbl_skin_b = QLabel("Player B: missing")

        row_a = QHBoxLayout()
        self.ed_skin_a = QLineEdit()
        self.ed_skin_a.setReadOnly(True)
        self.btn_browse_skin_a = QPushButton("Browse A")
        self.btn_reset_skin_a = QPushButton("Reset A")
        self.btn_browse_skin_a.clicked.connect(self.browse_skin_a_clicked.emit)
        self.btn_reset_skin_a.clicked.connect(self.reset_skin_a_clicked.emit)
        row_a.addWidget(self.ed_skin_a, stretch=1)
        row_a.addWidget(self.btn_browse_skin_a)
        row_a.addWidget(self.btn_reset_skin_a)

        row_b = QHBoxLayout()
        self.ed_skin_b = QLineEdit()
        self.ed_skin_b.setReadOnly(True)
        self.btn_browse_skin_b = QPushButton("Browse B")
        self.btn_reset_skin_b = QPushButton("Reset B")
        self.btn_browse_skin_b.clicked.connect(self.browse_skin_b_clicked.emit)
        self.btn_reset_skin_b.clicked.connect(self.reset_skin_b_clicked.emit)
        row_b.addWidget(self.ed_skin_b, stretch=1)
        row_b.addWidget(self.btn_browse_skin_b)
        row_b.addWidget(self.btn_reset_skin_b)

        skin_layout.addWidget(self.lbl_skin_a)
        skin_layout.addLayout(row_a)
        skin_layout.addSpacing(6)
        skin_layout.addWidget(self.lbl_skin_b)
        skin_layout.addLayout(row_b)

        layout.addWidget(cfg_box)
        layout.addSpacing(8)
        layout.addWidget(key_box)
        layout.addWidget(mouse_box)
        layout.addWidget(blocks_box)
        layout.addWidget(self.btn_apply_keybinds)
        layout.addSpacing(10)
        layout.addWidget(skin_box)
        layout.addStretch(1)

        self.tabs.addTab(self._wrap_scroll(page), "Settings")

    def _on_block_selection_changed(self) -> None:
        rows = self.block_table.selectionModel().selectedRows()
        if not rows:
            return
        r = rows[0].row()
        ix = self.block_table.item(r, 0)
        iy = self.block_table.item(r, 1)
        iz = self.block_table.item(r, 2)
        if ix is None or iy is None or iz is None:
            return
        self.blx.setValue(int(ix.text()))
        self.bly.setValue(int(iy.text()))
        self.blz.setValue(int(iz.text()))