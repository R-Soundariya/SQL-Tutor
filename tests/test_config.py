"""Unit tests for app.core.config. No network/DB calls."""

from app.core.config import Settings


def test_default_provider_is_anthropic() -> None:
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "anthropic"


def test_database_url_uses_pymysql_driver() -> None:
    settings = Settings(
        _env_file=None,
        db_user="alice",
        db_password="secret",
        db_host="db.example.com",
        db_port=3307,
        db_name="mydb",
    )
    assert settings.database_url == "mysql+pymysql://alice:secret@db.example.com:3307/mydb"
