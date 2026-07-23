"""Unit test for the safety-rejection path of get_explain_plan - unsafe SQL
must be rejected before the function ever tries to connect to a database."""

import pytest

from app.core.db.explain_plan import get_explain_plan
from app.core.db.query_runner import UnsafeQueryError


def test_get_explain_plan_rejects_unsafe_sql_before_connecting() -> None:
    with pytest.raises(UnsafeQueryError):
        get_explain_plan("DROP TABLE hr_employees")
