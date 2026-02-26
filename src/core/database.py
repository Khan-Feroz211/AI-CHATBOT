"""Database setup and connection management."""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.config import Config
from src.core.models import Base


class DatabaseManager:
    """Database connection and session management."""

    def __init__(self, config: Config):
        """Initialize database manager.

        Args:
            config: Configuration object with DATABASE_URL
        """
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._init_engine()

    def _init_engine(self):
        """Initialize SQLAlchemy engine based on config."""
        db_url = self.config.DATABASE_URL

        # SQLite specific configuration
        if "sqlite" in db_url:
            # Handle in-memory database for testing
            if "memory" in db_url or ":memory:" in db_url:
                engine_kwargs = {
                    "connect_args": {"check_same_thread": False},
                    "poolclass": StaticPool,
                }
            else:
                # File-based SQLite
                db_path = (
                    db_url.replace("sqlite:///", "")
                    .replace("sqlite:///", "")
                    .replace("sqlite:", "")
                )
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                engine_kwargs = {"connect_args": {"check_same_thread": False}}
        else:
            # PostgreSQL or other databases
            engine_kwargs = {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}

        self.engine = create_engine(db_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def init_db(self):
        """Initialize database - create all tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_db(self):
        """Drop all tables - used for testing."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get new database session.

        Returns:
            SQLAlchemy Session object
        """
        return self.SessionLocal()

    @contextmanager
    def get_session_context(self):
        """Context manager for database session.

        Usage:
            with db.get_session_context() as session:
                # use session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()


# Global database manager instance (initialized in Flask app)
_db_manager = None


def init_database(config: Config) -> DatabaseManager:
    """Initialize global database manager.

    Args:
        config: Configuration object

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    _db_manager = DatabaseManager(config)
    _db_manager.init_db()  # Create tables
    return _db_manager


def get_db() -> DatabaseManager:
    """Get global database manager.

    Returns:
        DatabaseManager instance

    Raises:
        RuntimeError: If database not initialized
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_manager


def get_session() -> Session:
    """Get new database session.

    Returns:
        SQLAlchemy Session object

    Raises:
        RuntimeError: If database not initialized
    """
    return get_db().get_session()


@contextmanager
def get_session_context():
    """Context manager for database session.

    Usage:
        with get_session_context() as session:
            # use session
    """
    session = get_db().get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
