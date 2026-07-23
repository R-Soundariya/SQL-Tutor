"""Integration-style tests for get_or_create_daily_challenge, using an
in-memory SQLite engine (injected via the module's optional `engine`
parameter - same pattern as app/core/db/sandbox/loader.py) so no real
MySQL server is needed. Only the caching/ORM behavior is under test here;
DDL text generation and query validation are exercised elsewhere."""

import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.daily_challenge.provider import get_or_create_daily_challenge
from tests.fakes import FakeLLMProvider

_VALID_RESPONSE = json.dumps(
    {
        "question": "Find all employees earning more than 80000.",
        "answer_query": "SELECT first_name FROM hr_employees WHERE salary > 80000",
    }
)


def _sqlite_engine():
    # StaticPool + check_same_thread=False so every connection from this
    # engine shares the same in-memory database - the SQLAlchemy-recommended
    # setup for :memory: SQLite, otherwise each connection gets its own.
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_creates_a_new_challenge_when_none_exists_for_the_date() -> None:
    engine = _sqlite_engine()
    llm = FakeLLMProvider(_VALID_RESPONSE)
    challenge_date = date(2026, 3, 1)

    challenge = get_or_create_daily_challenge(llm, challenge_date=challenge_date, engine=engine)

    assert challenge.challenge_date == challenge_date
    assert "employees" in challenge.question_text.lower()


def test_reuses_the_same_challenge_on_a_second_call_without_calling_the_llm_again() -> None:
    engine = _sqlite_engine()
    challenge_date = date(2026, 3, 2)

    first = get_or_create_daily_challenge(FakeLLMProvider(_VALID_RESPONSE), challenge_date=challenge_date, engine=engine)

    class ExplodingLLM(FakeLLMProvider):
        def generate(self, *args, **kwargs):
            raise AssertionError("Should not call the LLM again for an already-cached daily challenge")

    second = get_or_create_daily_challenge(ExplodingLLM(""), challenge_date=challenge_date, engine=engine)

    assert second == first


def test_different_dates_get_independent_challenges() -> None:
    engine = _sqlite_engine()
    llm = FakeLLMProvider(_VALID_RESPONSE)

    day1 = get_or_create_daily_challenge(llm, challenge_date=date(2026, 3, 3), engine=engine)
    day2 = get_or_create_daily_challenge(llm, challenge_date=date(2026, 3, 4), engine=engine)

    assert day1.challenge_date != day2.challenge_date
