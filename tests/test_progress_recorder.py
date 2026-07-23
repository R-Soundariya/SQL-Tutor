"""Unit test confirming record_attempt never raises, even when the
underlying database call fails - it's best-effort telemetry, not part of
the critical grading path that already succeeded by the time it's called."""

from sqlalchemy.exc import SQLAlchemyError

from app.core.progress import recorder


def test_record_attempt_swallows_database_errors(monkeypatch) -> None:
    monkeypatch.setattr(recorder, "ensure_progress_tables", lambda: None)

    def _raise_on_session():
        raise SQLAlchemyError("boom")

    monkeypatch.setattr(recorder, "get_session", _raise_on_session)

    # Must not raise.
    recorder.record_attempt(
        source="learn_sql",
        topic="GROUP BY",
        difficulty="Beginner",
        dataset_id="hr",
        is_correct=True,
    )
