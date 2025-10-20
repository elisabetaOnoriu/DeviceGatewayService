from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import Optional

class BaseWorker(ABC):
    NAME = "worker"

    def __init__(self, log, settings):
        self.log = log
        self.settings = settings

    @abstractmethod
    def perform_iteration(self) -> None:
        """Execute one unit of work (send/poll/process once)."""
        raise NotImplementedError

    def run(self, stop_event, sleep_sec: Optional[float] = None) -> str:
        self.log.info("[%s] started", self.NAME)
        try:
            while not stop_event.is_set():
                self.perform_iteration()
                if sleep_sec:
                    time.sleep(sleep_sec)
        except Exception as e:
            self.log.exception("[%s] crashed: %s", self.NAME, e)
            raise
        finally:
            self.on_stop()
            self.log.info("[%s] stopped", self.NAME)
        return f"{self.NAME} done"

    def on_stop(self) -> None:
        """Cleanup hook."""
        pass
