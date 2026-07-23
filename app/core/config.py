"""Centralized application configuration, loaded once from environment/.env."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """Typed application settings sourced from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM provider selection
    llm_provider: Literal["anthropic", "openai"] = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # MySQL connection
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "sql_interview_coach"

    # App
    app_env: Literal["development", "production"] = "development"
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        """SQLAlchemy connection URL for the configured MySQL database.

        Built via SQLAlchemy's URL.create() rather than an f-string so that
        special characters in the username/password (e.g. '@', ':', '/')
        are correctly percent-encoded instead of corrupting the URL.
        """
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so .env is parsed only once per process."""
    return Settings()
