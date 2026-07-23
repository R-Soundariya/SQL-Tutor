"""Retrieves MySQL's real EXPLAIN plan for a read-only query, so the Query
Optimizer's index/performance recommendations can be grounded in actual
data rather than guesswork."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text

from app.core.db.engine import get_engine
from app.core.db.query_runner import validate_read_only


def get_explain_plan(sql: str, engine: Engine | None = None) -> pd.DataFrame:
    """Run EXPLAIN on `sql` and return MySQL's query plan as a DataFrame.

    `sql` itself must be a single safe read-only statement (validated the
    same way as any other user-submitted query); EXPLAIN is prepended only
    for execution, not treated as part of the statement being validated.
    """
    validate_read_only(sql)
    engine = engine or get_engine()
    trimmed_sql = sql.strip().rstrip(";")
    with engine.connect() as conn:
        return pd.read_sql(text(f"EXPLAIN {trimmed_sql}"), conn)
