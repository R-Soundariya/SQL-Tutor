"""ORM model + table lifecycle for the persisted daily challenge question."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Engine, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.engine import Base, ensure_database_exists, get_engine
from app.core.timeutils import utc_now


class DailyChallengeRow(Base):
    """One day's persisted challenge question - generated once via the LLM,
    then reused for every visit on that calendar date."""

    __tablename__ = "daily_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    challenge_date: Mapped[date] = mapped_column(Date, unique=True)
    topic: Mapped[str] = mapped_column(String(100))
    difficulty: Mapped[str] = mapped_column(String(20))
    dataset_id: Mapped[str] = mapped_column(String(50))
    company: Mapped[str] = mapped_column(String(50))
    question_text: Mapped[str] = mapped_column(Text)
    answer_query: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


def ensure_daily_challenge_tables(engine: Engine | None = None) -> None:
    """Create the daily_challenges table if it doesn't exist yet.

    Accepts an optional engine (mirroring app/core/db/sandbox/loader.py's
    pattern) so tests can inject an in-memory SQLite engine instead of the
    real MySQL one.
    """
    if engine is None:
        ensure_database_exists()
    engine = engine or get_engine()
    Base.metadata.create_all(engine, tables=[DailyChallengeRow.__table__], checkfirst=True)
