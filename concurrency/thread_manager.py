from __future__ import annotations
import logging
from concurrent.futures import ThreadPoolExecutor, Future, wait
from threading import Event
from typing import Callable, Optional, List


class ThreadManager:
    """Tiny wrapper over ThreadPoolExecutor with a shared stop_event."""

    def __init__(self, logger: logging.Logger, max_workers: int = 5):
        self.log = logger
        self.max_workers = max_workers
        self._exec: Optional[ThreadPoolExecutor] = None
        self._futures: List[Future] = []
        self.stop_event = Event()

    def start(self) -> None:
        if self._exec is None:
            self._exec = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="worker")
            self.log.info("[ThreadManager] started (%d workers)", self.max_workers)

    def run(self, worker: Callable, *args, **kwargs) -> Future:
        """Submit worker(stop_event, *args, **kwargs)."""
        if self._exec is None:
            raise RuntimeError("ThreadManager not started. Call start() first.")
        future = self._exec.submit(worker, self.stop_event, *args, **kwargs)
        self._futures.append(future)
        return future

    def stop(self, timeout: float = 10.0) -> None:
        """Graceful stop: signal, wait a bit, shutdown."""
        self.log.info("[ThreadManager] stopping...")
        self.stop_event.set()

        if self._futures:
            done, _ = wait(self._futures, timeout=timeout)
            for i, future in enumerate(done):
                try:
                    self.log.info("[ThreadManager] worker %d OK: %s", i, future.result())
                except Exception as e:
                    self.log.error("[ThreadManager] worker %d FAILED: %s", i, e)

        if self._exec is not None:
            self._exec.shutdown(wait=False, cancel_futures=False)
            self._exec = None

        # make it reusable (optional)
        self._futures.clear()
        self.stop_event = Event()
        self.log.info("[ThreadManager] stopped.")
