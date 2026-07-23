"""Unit tests for read-only query validation. These test validate_read_only()
directly, so no database connection is needed."""

import pytest

from app.core.db.query_runner import UnsafeQueryError, validate_read_only


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM hr_employees",
        "  select first_name from hr_employees where salary > 50000",
        "WITH cte AS (SELECT 1 AS x) SELECT * FROM cte",
        "SELECT * FROM hr_employees;",
    ],
)
def test_valid_read_only_queries_pass(sql: str) -> None:
    validate_read_only(sql)  # should not raise


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "   ",
        "SELECT * FROM hr_employees; DROP TABLE hr_employees;",
        "UPDATE hr_employees SET salary = 0",
        "INSERT INTO hr_employees (employee_id) VALUES (1)",
        "DROP TABLE hr_employees",
        "DELETE FROM hr_employees",
        "ALTER TABLE hr_employees ADD COLUMN foo INT",
        "SELECT * FROM hr_employees INTO OUTFILE '/tmp/dump.csv'",
    ],
)
def test_unsafe_queries_are_rejected(sql: str) -> None:
    with pytest.raises(UnsafeQueryError):
        validate_read_only(sql)
