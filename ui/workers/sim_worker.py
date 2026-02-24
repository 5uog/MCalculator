# FILE: ui/workers/sim_worker.py
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from scene.world import World
from sim.jitter import JitterSpec
from sim.config import SimConfig
from sim.runner import run_sim

class SimWorker(QThread):
    progress = pyqtSignal(int, str)
    finished_payload = pyqtSignal(object)

    def __init__(self, world: World, jitter: JitterSpec, cfg: SimConfig):
        super().__init__()
        self._world = world
        self._jitter = jitter
        self._cfg = cfg
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        def stop_flag() -> bool:
            return self._stop

        def progress_cb(pct: float, stage: str, done: int, total: int) -> None:
            ip = int(round(pct))
            txt = f"{stage}: {done}/{total} ({ip}%)"
            self.progress.emit(ip, txt)

        stats_ab, stats_ba, res_ab, res_ba = run_sim(
            self._world,
            self._jitter,
            self._cfg,
            stop_flag=stop_flag,
            progress_cb=progress_cb,
        )
        self.finished_payload.emit((stats_ab, stats_ba, res_ab, res_ba))