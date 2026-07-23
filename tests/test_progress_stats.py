"""Unit tests for app.core.progress.stats. Every test passes a synthetic
DataFrame directly (matching the module's optional-DataFrame design), so
none of these need a database connection."""

from datetime import date, timedelta

import pandas as pd
import pytest

from app.core.progress.stats import (
    get_daily_activity,
    get_summary_stats,
    get_topic_mastery,
    get_weakest_topics,
)


def _make_attempts(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def test_empty_attempts_summary() -> None:
    empty = pd.DataFrame(columns=["id", "topic", "is_correct", "score", "created_at"])
    summary = get_summary_stats(empty)
    assert summary.total_attempts == 0
    assert summary.accuracy_pct == 0.0
    assert summary.average_score is None
    assert summary.current_streak_days == 0


def test_summary_computes_accuracy_and_average_score() -> None:
    now = pd.Timestamp.now()
    attempts = _make_attempts(
        [
            {"id": 1, "topic": "GROUP BY", "is_correct": True, "score": 10, "created_at": now},
            {"id": 2, "topic": "GROUP BY", "is_correct": False, "score": 2, "created_at": now},
            {"id": 3, "topic": "HAVING", "is_correct": True, "score": None, "created_at": now},
        ]
    )
    summary = get_summary_stats(attempts)
    assert summary.total_attempts == 3
    assert summary.accuracy_pct == pytest.approx(66.7, abs=0.1)
    assert summary.average_score == 6.0  # mean of 10 and 2; the None is excluded


def test_streak_counts_consecutive_days_ending_today() -> None:
    today = date.today()
    rows = [
        {"id": i, "topic": "x", "is_correct": True, "score": 5, "created_at": pd.Timestamp(today - timedelta(days=i))}
        for i in range(3)
    ]
    summary = get_summary_stats(_make_attempts(rows))
    assert summary.current_streak_days == 3


def test_streak_survives_missing_activity_today_but_present_yesterday() -> None:
    yesterday = date.today() - timedelta(days=1)
    attempts = _make_attempts(
        [{"id": 1, "topic": "x", "is_correct": True, "score": 5, "created_at": pd.Timestamp(yesterday)}]
    )
    summary = get_summary_stats(attempts)
    assert summary.current_streak_days == 1


def test_streak_resets_after_a_gap() -> None:
    two_days_ago = date.today() - timedelta(days=2)
    attempts = _make_attempts(
        [{"id": 1, "topic": "x", "is_correct": True, "score": 5, "created_at": pd.Timestamp(two_days_ago)}]
    )
    summary = get_summary_stats(attempts)
    assert summary.current_streak_days == 0


def test_topic_mastery_groups_and_sorts_ascending_by_accuracy() -> None:
    now = pd.Timestamp.now()
    attempts = _make_attempts(
        [
            {"id": 1, "topic": "A", "is_correct": True, "score": 10, "created_at": now},
            {"id": 2, "topic": "A", "is_correct": True, "score": 8, "created_at": now},
            {"id": 3, "topic": "B", "is_correct": False, "score": 2, "created_at": now},
        ]
    )
    mastery = get_topic_mastery(attempts)
    assert list(mastery["topic"]) == ["B", "A"]
    assert mastery.iloc[0]["accuracy_pct"] == 0.0
    assert mastery.iloc[1]["accuracy_pct"] == 100.0


def test_weakest_topics_requires_minimum_attempts() -> None:
    now = pd.Timestamp.now()
    attempts = _make_attempts(
        [
            # Only 1 attempt, incorrect - should NOT count (avoids one unlucky guess dominating).
            {"id": 1, "topic": "Lucky Miss", "is_correct": False, "score": 0, "created_at": now},
            # 2 attempts, both incorrect - should count.
            {"id": 2, "topic": "Consistent Weak", "is_correct": False, "score": 1, "created_at": now},
            {"id": 3, "topic": "Consistent Weak", "is_correct": False, "score": 1, "created_at": now},
        ]
    )
    weakest = get_weakest_topics(attempts, min_attempts=2)
    assert weakest == ["Consistent Weak"]


def test_daily_activity_aggregates_by_calendar_day() -> None:
    attempts = _make_attempts(
        [
            {"id": 1, "topic": "x", "is_correct": True, "score": 5, "created_at": pd.Timestamp("2026-01-01 10:00:00")},
            {"id": 2, "topic": "x", "is_correct": True, "score": 5, "created_at": pd.Timestamp("2026-01-01 18:00:00")},
            {"id": 3, "topic": "x", "is_correct": True, "score": 5, "created_at": pd.Timestamp("2026-01-02 09:00:00")},
        ]
    )
    daily = get_daily_activity(attempts)
    assert list(daily["attempts"]) == [2, 1]
