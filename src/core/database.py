"""Database setup and connection management."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.config import Config, normalize_database_url
from src.core.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session management."""

    def __init__(self, config: Config):
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._init_engine()

    def _init_engine(self) -> None:
        db_url = normalize_database_url(self.config.DATABASE_URL)

        if db_url.startswith("sqlite"):
            if "memory" in db_url or ":memory:" in db_url:
                engine_kwargs = {
                    "connect_args": {"check_same_thread": False},
                    "poolclass": StaticPool,
                }
            else:
                db_path = (
                    db_url.replace("sqlite:///", "", 1)
                    .replace("sqlite://", "", 1)
                    .replace("sqlite:", "", 1)
                )
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                engine_kwargs = {"connect_args": {"check_same_thread": False}}
        else:
            engine_kwargs = {
                "pool_pre_ping": True,
                "pool_size": int(os.environ.get("DB_POOL_SIZE", "5")),
                "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "10")),
                "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", "30")),
                "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", "1800")),
            }

        self.engine = create_engine(db_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False,
        )
        logger.info("Database engine initialized")

    def init_db(self) -> None:
        """Initialize database and create all tables."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database schema ensured with create_all")

    def drop_db(self) -> None:
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    @contextmanager
    def get_session_context(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        if self.engine:
            self.engine.dispose()


_db_manager: DatabaseManager | None = None


def init_database(config: Config) -> DatabaseManager:
    global _db_manager
    _db_manager = DatabaseManager(config)
    _db_manager.init_db()
    return _db_manager


def get_db() -> DatabaseManager:
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_manager


def get_session() -> Session:
    return get_db().get_session()


@contextmanager
def get_session_context():
    session = get_db().get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
