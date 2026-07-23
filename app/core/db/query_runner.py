"""Safely executes user-submitted, read-only SQL.

This is shared infrastructure: the Sandbox page uses it for ad-hoc
exploration today, and later phases (Practice/Interview scoring, Query
Optimizer, Explain SQL) reuse it any time a user's own SQL needs to run
against the database.
"""

from __future__ import annotations

import logging

import pandas as pd
import sqlparse
from sqlalchemy import Engine, text
from sqlparse.tokens import Keyword

from app.core.db.engine import get_engine

logger = logging.getLogger(__name__)

DEFAULT_ROW_LIMIT = 200

_FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "REPLACE",
    "CALL",
    "LOCK",
    "UNLOCK",
    "SET",
    "USE",
    "INTO",  # blocks `SELECT ... INTO OUTFILE`
}


class UnsafeQueryError(ValueError):
    """Raised when a submitted query fails read-only validation."""


def validate_read_only(sql: str) -> None:
    """Raise UnsafeQueryError unless `sql` is a single SELECT (or WITH ...
    SELECT) statement containing no data- or schema-modifying keywords."""
    if not sql or not sql.strip():
        raise UnsafeQueryError("Query is empty.")

    statements = [s for s in sqlparse.parse(sql) if s.token_first(skip_cm=True) is not None]
    if len(statements) != 1:
        raise UnsafeQueryError("Only a single SQL statement is allowed (no semicolon-separated batches).")

    statement = statements[0]
    first_token = statement.token_first(skip_cm=True)
    first_keyword = (first_token.value or "").upper() if first_token else ""
    if first_keyword not in ("SELECT", "WITH"):
        raise UnsafeQueryError(
            f"Only SELECT (or WITH ... SELECT) queries are allowed, got '{first_keyword}'."
        )

    found_keywords = {tok.value.upper() for tok in statement.flatten() if tok.ttype in Keyword}
    forbidden_found = found_keywords & _FORBIDDEN_KEYWORDS
    if forbidden_found:
        raise UnsafeQueryError(f"Query contains disallowed keyword(s): {', '.join(sorted(forbidden_found))}")


def run_read_only_query(
    sql: str,
    engine: Engine | None = None,
    row_limit: int = DEFAULT_ROW_LIMIT,
) -> pd.DataFrame:
    """Validate and execute a read-only SQL query, returning at most `row_limit` rows.

    Note: the query is wrapped as `SELECT * FROM (<sql>) AS t LIMIT n` to
    enforce the cap regardless of what the user wrote. MySQL does not
    formally guarantee that an inner ORDER BY survives this wrapping, so
    exact row ordering on large/ambiguous result sets isn't guaranteed here.
    """
    validate_read_only(sql)
    engine = engine or get_engine()

    trimmed_sql = sql.strip().rstrip(";")
    wrapped_sql = text(f"SELECT * FROM ( {trimmed_sql} ) AS sandbox_subquery LIMIT :row_limit")

    logger.debug("Executing sandbox query (limit=%d): %s", row_limit, trimmed_sql)
    with engine.connect() as conn:
        return pd.read_sql(wrapped_sql, conn, params={"row_limit": row_limit})
