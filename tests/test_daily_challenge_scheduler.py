"""Unit tests for daily challenge date-based scheduling. Pure function -
no database or LLM involved."""

from datetime import date

from app.core.daily_challenge.provider import schedule_for_date
from app.core.db.sandbox.schema import DATASETS
from app.core.practice.constants import DIFFICULTIES, TOPICS


def test_schedule_is_deterministic_for_the_same_date() -> None:
    d = date(2026, 7, 23)
    assert schedule_for_date(d) == schedule_for_date(d)


def test_schedule_returns_valid_options() -> None:
    dataset_id, topic, difficulty = schedule_for_date(date(2026, 7, 23))
    assert dataset_id in DATASETS
    assert topic in TOPICS
    assert difficulty in DIFFICULTIES


def test_schedule_varies_across_different_dates() -> None:
    schedules = {schedule_for_date(date(2026, 1, day)) for day in range(1, 15)}
    assert len(schedules) > 1
