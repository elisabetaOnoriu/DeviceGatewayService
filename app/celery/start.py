import subprocess, sys, shlex
from typing import Optional

def spawn(role: str, options: Optional[str] = None) -> subprocess.Popen:
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "app.celery.config.celery_app",
        role,
        "--loglevel=warning",
    ]

    cmd.extend(shlex.split(options or ""))
    return subprocess.Popen(cmd)
