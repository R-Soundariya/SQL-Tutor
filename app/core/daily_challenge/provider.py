"""Fetches or creates the deterministic daily challenge question, persisted
per calendar day so every visit that day sees the same question without
another LLM call."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import date

from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.daily_challenge.models import DailyChallengeRow, ensure_daily_challenge_tables
from app.core.db.engine import get_engine
from app.core.db.sandbox.schema import DATASETS
from app.core.llm.base import LLMProvider
from app.core.practice.constants import DIFFICULTIES, TOPICS
from app.core.practice.question_generator import generate_question
from app.core.timeutils import utc_now

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DailyChallengeData:
    """A single day's challenge question, independent of the ORM row that stores it."""

    challenge_date: date
    topic: str
    difficulty: str
    dataset_id: str
    company: str
    question_text: str
    answer_query: str


def schedule_for_date(challenge_date: date) -> tuple[str, str, str]:
    """Deterministically pick (dataset_id, topic, difficulty) for a given
    calendar date, so the category is the same for every visitor on that
    day without needing to persist the choice ahead of the question itself."""
    seed = int(challenge_date.strftime("%Y%m%d"))
    rng = random.Random(seed)
    dataset_id = rng.choice(list(DATASETS.keys()))
    topic = rng.choice(TOPICS)
    difficulty = rng.choice(DIFFICULTIES)
    return dataset_id, topic, difficulty


def _row_to_data(row: DailyChallengeRow) -> DailyChallengeData:
    return DailyChallengeData(
        challenge_date=row.challenge_date,
        topic=row.topic,
        difficulty=row.difficulty,
        dataset_id=row.dataset_id,
        company=row.company,
        question_text=row.question_text,
        answer_query=row.answer_query,
    )


def get_or_create_daily_challenge(
    llm: LLMProvider,
    challenge_date: date | None = None,
    engine: Engine | None = None,
) -> DailyChallengeData:
    """Return today's (or `challenge_date`'s) challenge, generating and
    persisting it via `llm` on the first request of the day and reusing the
    stored row - no further LLM calls - on every request after that."""
    challenge_date = challenge_date or date.today()
    ensure_daily_challenge_tables(engine)
    engine = engine or get_engine()

    with Session(engine) as session:
        existing = session.scalar(select(DailyChallengeRow).where(DailyChallengeRow.challenge_date == challenge_date))
        if existing is not None:
            return _row_to_data(existing)

    dataset_id, topic, difficulty = schedule_for_date(challenge_date)
    question = generate_question(llm, dataset_id, topic, difficulty, company="Any / Generic")

    new_row = DailyChallengeRow(
        challenge_date=challenge_date,
        topic=question.topic,
        difficulty=question.difficulty,
        dataset_id=question.dataset_id,
        company=question.company,
        question_text=question.question,
        answer_query=question.answer_query,
        created_at=utc_now(),
    )

    try:
        with Session(engine) as session:
            session.add(new_row)
            session.commit()
    except IntegrityError:
        logger.info("Daily challenge for %s was already created by a concurrent request.", challenge_date)

    with Session(engine) as session:
        existing = session.scalar(select(DailyChallengeRow).where(DailyChallengeRow.challenge_date == challenge_date))
        return _row_to_data(existing)
