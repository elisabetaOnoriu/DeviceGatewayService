# tests/conftest.py
from __future__ import annotations

import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
# Import models so they are registered in Base.metadata before create_all
from app.models.client import Client  # noqa: F401
from app.models.device import Device  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def _force_test_env() -> None:
    """
    Ensure a minimal test environment is always set.
    If the application depends on environment variables such as DATABASE_URL,
    we provide a dummy SQLite in-memory URL here.
    """
    os.environ.setdefault("ENV", "TEST")
    os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")


@pytest.fixture(scope="session")
def engine():
    """
    Create a shared SQLite in-memory engine for the whole test session.

    - Uses StaticPool to ensure all connections share the same in-memory database.
    - Enables foreign key checks explicitly for SQLite (disabled by default).
    - Creates all database tables once before the tests start.
    - Drops all tables at the end of the test session (optional cleanup).
    """
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        """
        Enable foreign key support in SQLite for every new connection.
        Without this, SQLite ignores foreign key constraints by default.
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(eng)


@pytest.fixture(scope="session")
def SessionLocal(engine):
    """
    Provide a factory for creating new SQLAlchemy Session objects
    bound to the in-memory engine used in tests.
    """
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@pytest.fixture(autouse=True)
def db_session(SessionLocal, engine) -> Session:
    """
    Provide a fresh database session for each test.

    Each test runs inside a database transaction:
    - A connection is opened and a transaction is started.
    - A new session is bound to this connection.
    - The test runs using this session.
    - At the end of the test, the transaction is rolled back,
      ensuring the database is restored to its initial clean state.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session: Session = SessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def xml_template() -> str:
    """
    Load and return a valid XML template string for tests.

    Resolution order:
    1) tests/message_template.xml
    2) app/templates/message_template.xml
    3) Inline fallback (minimal XML with the expected structure and namespace)

    The returned XML has all ${...} placeholders replaced with test values.
    """
    candidates = [
        Path(__file__).parent / "message_template.xml",
        Path(__file__).parents[1] / "app" / "templates" / "message_template.xml",
    ]

    xml_text: str | None = None
    for p in candidates:
        if p.exists():
            xml_text = p.read_text(encoding="utf-8")
            break

    if xml_text is None:
        # Inline fallback used only if no file was found.
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<Message xmlns="urn:example:device-message" version="1.0">
  <Header>
    <MessageID>${message_id}</MessageID>
    <DeviceID>${device_id}</DeviceID>
    <ClientID>${client_id}</ClientID>
    <Timestamp>${timestamp}</Timestamp>
  </Header>
  <Body>
    <Sensor>${sensor}</Sensor>
    <Value>${value}</Value>
    <Unit>${unit}</Unit>
    <Meta>
      <Firmware>${firmware}</Firmware>
      <Source>${source}</Source>
    </Meta>
  </Body>
</Message>""".strip()

    filled = (
        xml_text.replace("${message_id}", "m-1")
                .replace("${device_id}", "1")
                .replace("${client_id}", "2")
                .replace("${timestamp}", "2025-08-19T12:34:56Z")
                .replace("${sensor}", "temp")
                .replace("${value}", "23")
                .replace("${unit}", "C")
                .replace("${firmware}", "1.0.0")
                .replace("${source}", "test")
    )
    return filled
