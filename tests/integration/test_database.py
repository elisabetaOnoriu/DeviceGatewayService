import sys
import importlib

import pytest
from sqlalchemy import text

# candidate module paths; pick the one that exists in your project
CANDIDATES = ("app.database", "app.db", "app.config.database")


def _reload_db():
    """Import DB module fresh so top-level code re-executes."""
    importlib.invalidate_caches()
    last = None
    for name in CANDIDATES:
        sys.modules.pop(name, None)
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as e:
            last = e
    raise last or ModuleNotFoundError("DB module not found")


def test_database_url_required(monkeypatch):
    """If DATABASE_URL is missing, the DB module should raise at import time."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        _reload_db()


@pytest.mark.parametrize("url", ["sqlite+pysqlite:///:memory:"])
def test_engine_created(monkeypatch, url):
    """Engine should be created when DATABASE_URL is set."""
    monkeypatch.setenv("DATABASE_URL", url)
    db = _reload_db()
    assert str(db.engine.url).startswith("sqlite")


@pytest.mark.parametrize("url", ["sqlite+pysqlite:///:memory:"])
def test_sessionlocal(monkeypatch, url):
    """SessionLocal should create a working session."""
    monkeypatch.setenv("DATABASE_URL", url)
    db = _reload_db()
    s = db.SessionLocal()
    try:
        assert s.execute(text("SELECT 1")).scalar() == 1
    finally:
        s.close()
