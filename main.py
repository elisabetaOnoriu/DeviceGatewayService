from __future__ import annotations
import time
from app.gateway.runtime import bootstrap, build_workers

def main() -> None:
    log, redis, tm = bootstrap()
    workers = build_workers(log, redis)
    for w in workers:
        tm.submit_worker(w.run)
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        tm.shutdown()

if __name__ == "__main__":
    main()
