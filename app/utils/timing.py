from __future__ import annotations
import threading
import time

def stop_aware_sleep(seconds: float, stop_event: threading.Event, step: float = 0.1) -> None:
    """
    Doarme în pași mici pentru a verifica frecvent dacă s-a cerut oprirea.
    """
    remaining = seconds
    while remaining > 0 and not stop_event.is_set():
        chunk = min(step, remaining)
        time.sleep(chunk)
        remaining -= chunk
