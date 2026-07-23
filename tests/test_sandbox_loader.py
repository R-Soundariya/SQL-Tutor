"""Regression test: load_all_datasets() must ensure the database exists
before loading, the same way calling load_dataset() directly (with no
engine override) already does. Caught via a real run against MySQL - the
UI's per-dataset "Load / Reset" button called load_dataset() directly and
never hit this, but the load_sandbox_data.py CLI script (via
load_all_datasets()) skipped database creation entirely. Uses
monkeypatching so no real database connection is needed here."""

from app.core.db.sandbox import loader


def test_load_all_datasets_ensures_database_exists_when_no_engine_given(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(loader, "ensure_database_exists", lambda: calls.append("ensure_database_exists"))
    monkeypatch.setattr(loader, "load_dataset", lambda dataset_id, engine: {})
    monkeypatch.setattr(loader, "get_engine", lambda: "fake-engine")

    loader.load_all_datasets()

    assert calls == ["ensure_database_exists"]


def test_load_all_datasets_does_not_ensure_database_exists_when_engine_is_given(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(loader, "ensure_database_exists", lambda: calls.append("ensure_database_exists"))
    monkeypatch.setattr(loader, "load_dataset", lambda dataset_id, engine: {})

    loader.load_all_datasets(engine="already-provided-engine")

    assert calls == []
