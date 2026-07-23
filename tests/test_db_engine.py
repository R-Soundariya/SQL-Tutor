"""Unit tests for app.core.db.engine. create_engine() is lazy, so this does
not require a real MySQL server."""

from sqlalchemy.engine import Engine

from app.core.db.engine import get_engine


def test_get_engine_returns_engine_without_connecting() -> None:
    engine = get_engine()
    assert isinstance(engine, Engine)
    assert engine.url.drivername == "mysql+pymysql"
