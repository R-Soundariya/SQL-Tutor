"""SQLAlchemy engine/session management for the MySQL database."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


_engine = None
_SessionLocal: sessionmaker | None = None


def get_engine():
    """Return a lazily-created, process-wide SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    return _engine


def get_session_factory() -> sessionmaker:
    """Return a lazily-created sessionmaker bound to the shared engine."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionLocal


@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional session as a context manager."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> tuple[bool, str]:
    """Attempt a lightweight round-trip query against the configured database.

    Returns (success, message) so callers (e.g. the Settings page) can display
    a status without needing to catch exceptions themselves.
    """
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Connected to MySQL successfully."
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI verbatim
        logger.warning("Database connection check failed: %s", exc)
        return False, str(exc)
