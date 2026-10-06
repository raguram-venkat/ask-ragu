"""Single-flight background sync (ADR-0005): one run at a time; triggers mid-run coalesce.

Ten pushes during one sync cost one extra run, not ten: a trigger while running only sets
`dirty`, and the worker loops once more when it finishes. A crash loses the in-flight run;
Task 8's startup reconciliation catches up from last_commit.
"""

import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime

log = logging.getLogger(__name__)


class SyncRunner:
    def __init__(self, job: Callable[[], object]):
        self._job = job
        self._lock = threading.Lock()  # guards the two flags below
        self._running = False
        self._dirty = False
        self.last: dict | None = None  # outcome of the last finished run, for /index/status

    @property
    def running(self) -> bool:
        return self._running

    def trigger(self) -> bool:
        """Start a run in a background thread, or mark one pending. True if a thread started."""
        with self._lock:
            if self._running:
                self._dirty = True
                return False
            self._running = True
        threading.Thread(target=self._loop, name="sync", daemon=True).start()
        return True

    def _loop(self) -> None:
        while True:
            try:
                result = {"ok": True, "result": str(self._job())}
            except Exception as e:  # keep the runner alive; the next trigger retries
                log.exception("sync failed")
                result = {"ok": False, "error": f"{type(e).__name__}: {e}"}
            self.last = {"finished_at": datetime.now(UTC).isoformat(timespec="seconds"), **result}
            with self._lock:
                if not self._dirty:
                    self._running = False
                    return
                self._dirty = False
