from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from src.runtime import get_settings


@dataclass
class TaskSnapshot:
    status: str = "idle"
    result: str = ""
    started_at: float | None = None
    finished_at: float | None = None
    last_error: str = ""


class LocalMaintenanceScheduler:
    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.enable_local_maintenance
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._snapshots = {
            "ingest": TaskSnapshot(),
            "reflect": TaskSnapshot(),
            "growth": TaskSnapshot(),
            "review": TaskSnapshot(),
            "nemesis": TaskSnapshot(),
        }

    def start(self) -> None:
        if not self.enabled:
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="omni-local-maintenance", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def run_now(self, task_name: str) -> None:
        if task_name not in self._snapshots:
            raise ValueError(f"Unknown maintenance task: {task_name}")
        threading.Thread(
            target=self._execute_task,
            args=(task_name,),
            name=f"omni-maintenance-{task_name}",
            daemon=True,
        ).start()

    def get_status(self) -> dict:
        with self._lock:
            return {
                "enabled": self.enabled,
                "running": bool(self._thread and self._thread.is_alive()),
                "tasks": {
                    name: {
                        "status": snapshot.status,
                        "result": snapshot.result,
                        "started_at": snapshot.started_at,
                        "finished_at": snapshot.finished_at,
                        "last_error": snapshot.last_error,
                    }
                    for name, snapshot in self._snapshots.items()
                },
            }

    def _run_loop(self) -> None:
        next_ingest = time.time() + self.settings.maintenance_ingest_interval_seconds
        next_reflect = time.time() + self.settings.maintenance_reflection_interval_seconds
        next_growth = time.time() + self.settings.maintenance_growth_interval_seconds
        next_review = time.time() + self.settings.maintenance_review_interval_seconds

        while not self._stop_event.is_set():
            now = time.time()
            if now >= next_ingest:
                self._execute_task("ingest")
                next_ingest = now + self.settings.maintenance_ingest_interval_seconds
            if now >= next_reflect:
                self._execute_task("reflect")
                next_reflect = now + self.settings.maintenance_reflection_interval_seconds
            if now >= next_growth:
                self._execute_task("growth")
                next_growth = now + self.settings.maintenance_growth_interval_seconds
            if now >= next_review:
                self._execute_task("review")
                next_review = now + self.settings.maintenance_review_interval_seconds
            self._stop_event.wait(1.0)

    def _execute_task(self, task_name: str) -> None:
        task_map: dict[str, Callable[[], str]] = {
            "ingest": self._run_ingest,
            "reflect": self._run_reflect,
            "growth": self._run_growth,
            "review": self._run_review,
            "nemesis": self._run_nemesis,
        }
        snapshot = self._snapshots[task_name]
        with self._lock:
            snapshot.status = "running"
            snapshot.started_at = time.time()
            snapshot.finished_at = None
            snapshot.last_error = ""

        try:
            result = task_map[task_name]()
            with self._lock:
                snapshot.status = "ok"
                snapshot.result = str(result)
                snapshot.finished_at = time.time()
        except Exception as exc:
            with self._lock:
                snapshot.status = "error"
                snapshot.result = ""
                snapshot.last_error = str(exc)
                snapshot.finished_at = time.time()

    def _run_ingest(self) -> str:
        from src.maintenance.tasks import process_cache_to_memory

        return process_cache_to_memory(batch_size=100)

    def _run_reflect(self) -> str:
        from src.maintenance.tasks import process_cache_to_memory, autonomous_reflection

        process_cache_to_memory(batch_size=100)
        return autonomous_reflection(sample_size=250)

    def _run_growth(self) -> str:
        from src.maintenance.tasks import exponential_growth_cycle

        return exponential_growth_cycle()

    def _run_nemesis(self) -> str:
        from src.maintenance.tasks import trigger_nemesis

        return trigger_nemesis()

    def _run_review(self) -> str:
        from src.training.service import TrainingService

        review = TrainingService().run_improvement_cycle(trigger="scheduler_review")
        return (
            f"Self-review complete. Readiness {review.get('readiness_score', 0.0):.2f}. "
            f"Open remediations: {len(review.get('remediation_queue', []))}."
        )


_scheduler: LocalMaintenanceScheduler | None = None


def get_local_scheduler() -> LocalMaintenanceScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = LocalMaintenanceScheduler()
    return _scheduler
