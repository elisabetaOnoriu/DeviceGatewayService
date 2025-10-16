from __future__ import annotations
import logging
from concurrent.futures import ThreadPoolExecutor, Future, wait, FIRST_EXCEPTION
from threading import Event
from typing import Callable, Optional


class ThreadManager:

    def __init__(self, logger: logging.Logger, max_workers: int = 5):
        self.log = logger
        self.max_workers = max_workers
        self._exec: Optional[ThreadPoolExecutor] = None
        self._futures: list[Future] = []
        self.stop_event = Event()


    def start(self) -> None:
        if self._exec is not None:
            return
        self._exec = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="worker")
        self.log.info("[ThreadManager] started (%d workers)", self.max_workers)

    def stop(self, timeout: float = 10.0, cancel_queue: bool = False) -> None:
        self.log.info("[ThreadManager] stopping...")
        self.stop_event.set()

        if self._futures:
            done, not_done = wait(self._futures, timeout=timeout, return_when=FIRST_EXCEPTION)
            for i, future in enumerate(self._futures):
                if future in done:
                    try:
                        res = future.result()
                        self.log.info("[ThreadManager] worker %d OK: %s", i, res)
                    except Exception as e:
                        self.log.error("[ThreadManager] worker %d FAILED: %s", i, e)

            if cancel_queue:
                for future in not_done:
                    future.cancel()

        if self._exec is not None:
            self._exec.shutdown(wait=False, cancel_futures=False)
            self._exec = None

        self.log.info("[ThreadManager] stopped.")


    def run(self, worker: Callable, *args, **kwargs) -> Future:
        if self._exec is None:
            raise RuntimeError("ThreadManager not started. Call start() first.")
        future = self._exec.submit(worker, self.stop_event, *args, **kwargs)
        self._futures.append(future)
        return future


    def is_running(self) -> bool:
        return any(not f.done() for f in self._futures)

    def status(self) -> dict:
        total = len(self._futures)
        done = sum(f.done() for f in self._futures)
        return {
            "total": total,
            "running": total - done,
            "completed": done,
            "stop_requested": self.stop_event.is_set(),
        }

    def __enter__(self) -> "ThreadManager":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop(timeout=10.0)
