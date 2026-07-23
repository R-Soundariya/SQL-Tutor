"""Logs a graded attempt for the Progress Dashboard to aggregate later."""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.db.engine import get_session
from app.core.progress.models import Attempt, ensure_progress_tables
from app.core.timeutils import utc_now

logger = logging.getLogger(__name__)


def record_attempt(
    source: str,
    topic: str,
    difficulty: str,
    dataset_id: str,
    is_correct: bool,
    score: int | None = None,
) -> None:
    """Best-effort log of one attempt. Never raises - a logging failure must
    not break a grading flow that already succeeded; it's only telemetry
    for the Progress Dashboard, not the feature itself."""
    try:
        ensure_progress_tables()
        with get_session() as session:
            session.add(
                Attempt(
                    source=source,
                    topic=topic,
                    difficulty=difficulty,
                    dataset_id=dataset_id,
                    is_correct=is_correct,
                    score=score,
                    created_at=utc_now(),
                )
            )
    except SQLAlchemyError:
        logger.warning("Could not record progress attempt (source=%s, topic=%s)", source, topic, exc_info=True)
