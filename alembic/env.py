"""Alembic environment for BazaarBot.

Imports all ORM models so Alembic autogenerate can detect them.
Converts the asyncpg DATABASE_URL to a psycopg2-compatible sync URL
for Alembic's standard migration runner.
"""
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Make the project root importable ─────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Import app config ─────────────────────────────────────────────────────
from bazaarbot.config import Config

# ── Import Base and all models so Alembic can see them ───────────────────
from bazaarbot.database_pg import Base  # noqa: F401
import bazaarbot.models  # noqa: F401 — registers all ORM classes on Base

# ── Alembic Config object ─────────────────────────────────────────────────
config = context.config

# Interpret the config file's logging configuration.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Convert asyncpg URL → psycopg2 for synchronous Alembic operations.
_async_url: str = Config.DATABASE_URL
_sync_url: str = _async_url.replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
)
config.set_main_option("sqlalchemy.url", _sync_url)

target_metadata = Base.metadata


# ── Offline migrations (no live DB connection) ────────────────────────────

def run_migrations_offline() -> None:
    """Emit SQL to stdout without a DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (live DB connection) ────────────────────────────────

def run_migrations_online() -> None:
    """Run migrations with an active DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
