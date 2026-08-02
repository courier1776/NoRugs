from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from norugs_scraper.settings import Settings

LOG = logging.getLogger("norugs.live")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class UpdateState:
    running: bool = False
    enabled: bool = False
    interval_seconds: int = 60
    last_started_at: str | None = None
    last_completed_at: str | None = None
    last_success_at: str | None = None
    last_error: str | None = None
    cycles_completed: int = 0
    latest_counts: dict[str, int] = field(default_factory=dict)


class LiveUpdateService:
    """Single-process periodic collector with overlap protection."""

    def __init__(
        self,
        settings: Settings,
        config_path: Path,
        interval_seconds: int,
        collector: Callable[..., dict[str, int]] | None = None,
    ) -> None:
        self.settings = settings
        self.config_path = config_path
        self.interval_seconds = max(15, interval_seconds)
        if collector is None:
            from norugs_scraper.collector import collect_once
            collector = collect_once
        self.collector = collector
        self._state = UpdateState(interval_seconds=self.interval_seconds)
        self._state_lock = threading.Lock()
        self._run_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, *, run_immediately: bool = True) -> None:
        with self._state_lock:
            if self._thread and self._thread.is_alive():
                return
            self._state.enabled = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            args=(run_immediately,),
            name="norugs-live-updater",
            daemon=True,
        )
        self._thread.start()
        LOG.info("Live updater started with a %s-second interval", self.interval_seconds)

    def stop(self) -> None:
        self._stop_event.set()
        with self._state_lock:
            self._state.enabled = False

    def trigger(self) -> bool:
        """Start an immediate refresh in a daemon thread; reject overlaps."""
        if self._run_lock.locked():
            return False
        threading.Thread(target=self.run_once, name="norugs-manual-refresh", daemon=True).start()
        return True

    def run_once(self) -> bool:
        if not self._run_lock.acquire(blocking=False):
            return False
        with self._state_lock:
            self._state.running = True
            self._state.last_started_at = utc_now_iso()
            self._state.last_error = None
        try:
            counts = self.collector(self.settings, self.config_path, provider="all")
            completed = utc_now_iso()
            with self._state_lock:
                self._state.latest_counts = counts
                self._state.last_completed_at = completed
                self._state.last_success_at = completed
                self._state.cycles_completed += 1
            LOG.info("Live update completed: %s", counts)
            return True
        except Exception as exc:  # keep the web process alive on provider/db failure
            LOG.exception("Live update failed")
            with self._state_lock:
                self._state.last_completed_at = utc_now_iso()
                self._state.last_error = str(exc)
            return False
        finally:
            with self._state_lock:
                self._state.running = False
            self._run_lock.release()

    def status(self) -> dict[str, object]:
        with self._state_lock:
            return asdict(self._state)

    def _loop(self, run_immediately: bool) -> None:
        if run_immediately and not self._stop_event.is_set():
            self.run_once()
        while not self._stop_event.wait(self.interval_seconds):
            self.run_once()
