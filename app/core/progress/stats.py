"""Aggregate statistics computed from logged practice attempts, for the
Progress Dashboard.

Every function accepts an optional pre-loaded `attempts` DataFrame (falling
back to a fresh load from the database when omitted) so the aggregation
logic is fully unit-testable with synthetic data, with no DB required.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from app.core.db.engine import get_engine
from app.core.progress.models import ensure_progress_tables


@dataclass(frozen=True)
class SummaryStats:
    total_attempts: int
    accuracy_pct: float
    average_score: float | None
    current_streak_days: int


def load_attempts() -> pd.DataFrame:
    """Return every logged attempt, oldest first. Empty (but correctly
    shaped) DataFrame if nothing has been logged yet."""
    ensure_progress_tables()
    engine = get_engine()
    attempts = pd.read_sql("SELECT * FROM progress_attempts ORDER BY created_at", engine)
    if not attempts.empty:
        attempts["created_at"] = pd.to_datetime(attempts["created_at"])
    return attempts


def _compute_current_streak(activity_dates: set[date]) -> int:
    """A streak survives until a full calendar day is skipped - it doesn't
    break just because today has no activity yet."""
    if not activity_dates:
        return 0

    day = date.today()
    if day not in activity_dates:
        day -= timedelta(days=1)
        if day not in activity_dates:
            return 0

    streak = 0
    while day in activity_dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def get_summary_stats(attempts: pd.DataFrame | None = None) -> SummaryStats:
    attempts = load_attempts() if attempts is None else attempts

    if attempts.empty:
        return SummaryStats(total_attempts=0, accuracy_pct=0.0, average_score=None, current_streak_days=0)

    total_attempts = len(attempts)
    accuracy_pct = round(float(attempts["is_correct"].astype(bool).mean()) * 100, 1)

    scored = attempts["score"].dropna()
    average_score = round(float(scored.mean()), 2) if not scored.empty else None

    activity_dates = {timestamp.date() for timestamp in attempts["created_at"]}
    streak = _compute_current_streak(activity_dates)

    return SummaryStats(
        total_attempts=total_attempts,
        accuracy_pct=accuracy_pct,
        average_score=average_score,
        current_streak_days=streak,
    )


def get_topic_mastery(attempts: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per-topic attempts/accuracy/average score, sorted by accuracy
    ascending (weakest first)."""
    attempts = load_attempts() if attempts is None else attempts
    if attempts.empty:
        return pd.DataFrame(columns=["topic", "attempts", "accuracy_pct", "average_score"])

    def _accuracy_pct(is_correct: pd.Series) -> float:
        return round(float(is_correct.astype(bool).mean()) * 100, 1)

    def _average_score(score: pd.Series) -> float | None:
        non_null = score.dropna()
        return round(float(non_null.mean()), 2) if not non_null.empty else None

    grouped = attempts.groupby("topic").agg(
        attempts=("id", "count"),
        accuracy_pct=("is_correct", _accuracy_pct),
        average_score=("score", _average_score),
    )
    return grouped.reset_index().sort_values("accuracy_pct", ascending=True)


def get_weakest_topics(attempts: pd.DataFrame | None = None, min_attempts: int = 2, top_n: int = 5) -> list[str]:
    """Topics with the lowest accuracy, requiring at least `min_attempts` so
    a single unlucky guess doesn't dominate the list."""
    mastery = get_topic_mastery(attempts)
    qualifying = mastery[mastery["attempts"] >= min_attempts]
    return list(qualifying.sort_values("accuracy_pct").head(top_n)["topic"])


def get_daily_activity(attempts: pd.DataFrame | None = None) -> pd.DataFrame:
    """Attempts per calendar day, oldest first, for charting activity over time."""
    attempts = load_attempts() if attempts is None else attempts
    if attempts.empty:
        return pd.DataFrame(columns=["date", "attempts"])

    daily = (
        attempts.assign(date=attempts["created_at"].dt.date)
        .groupby("date")
        .size()
        .reset_index(name="attempts")
        .sort_values("date")
    )
    return daily
