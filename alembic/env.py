from logging.config import fileConfig
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Alembic config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Add project root to PYTHONPATH (alembic/ is in project root)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# --- Load .env (optional but useful)
try:
    from dotenv import load_dotenv  # python-dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass  # if python-dotenv is not installed, set env vars in shell

# --- Import Base and models, so autogenerate can "see" the tables
from app.models.base import Base  # noqa: E402
# import the modules that define models (just importing is enough)
from app.models import device  # noqa: F401
# if you also have clients, status etc., import them here:
# from app.models import client  # noqa: F401
# from app.models import status  # noqa: F401

target_metadata = Base.metadata

# --- Determine DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # fallback to alembic.ini if needed
    DATABASE_URL = config.get_main_option("sqlalchemy.url")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set (in .env or alembic.ini)")

def run_migrations_offline() -> None:
    """Offline mode – no Engine, only URL."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Online mode – with Engine and real connection."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
