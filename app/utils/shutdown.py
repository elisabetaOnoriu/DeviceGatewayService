import logging
import signal
import threading

class ShutdownHandler:
    """
    Atașează handler-e pentru SIGINT/SIGTERM și expune un threading.Event
    pe care îl poți folosi ca stop flag.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.log = logger or logging.getLogger("shutdown")
        self.stop_event = threading.Event()
        self._install()

    def _install(self) -> None:
        def _handler(signum, frame):
            self.log.info("Signal %s received → shutting down ...", signum)
            self.stop_event.set()

        for name in ("SIGINT", "SIGTERM"):
            if hasattr(signal, name):
                signal.signal(getattr(signal, name), _handler)
