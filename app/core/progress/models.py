"""ORM model + table lifecycle for logged practice attempts.

This is the app's own persistent table (as opposed to the sandbox
datasets, which are practice data the user queries) - it lives on Base
from app.core.db.engine, reserved since Phase 1 for exactly this."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.engine import Base, ensure_database_exists, get_engine
from app.core.timeutils import utc_now


class Attempt(Base):
    """One graded attempt at a question, logged by Learn SQL, Practice
    Questions, or Mock Interview."""

    __tablename__ = "progress_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(30))  # "learn_sql" | "practice_questions" | "mock_interview"
    topic: Mapped[str] = mapped_column(String(100))
    difficulty: Mapped[str] = mapped_column(String(20))
    dataset_id: Mapped[str] = mapped_column(String(50))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


_tables_ensured = False


def ensure_progress_tables() -> None:
    """Create the progress_attempts table if it doesn't exist yet.

    Cheap to call repeatedly (checkfirst=True), but cached at module level
    so it's not a round trip before every single insert or query.
    """
    global _tables_ensured
    if _tables_ensured:
        return
    ensure_database_exists()
    Base.metadata.create_all(get_engine(), tables=[Attempt.__table__], checkfirst=True)
    _tables_ensured = True
