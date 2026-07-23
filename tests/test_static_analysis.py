"""Unit tests for app.core.optimizer.static_analysis. Pure string analysis
- no database connection, no LLM call."""

from app.core.optimizer.static_analysis import analyze_query


def test_detects_select_star() -> None:
    findings = analyze_query("SELECT * FROM hr_employees")
    assert any(f.category == "Unnecessary SELECT *" for f in findings)


def test_detects_missing_where() -> None:
    findings = analyze_query("SELECT first_name FROM hr_employees")
    assert any(f.category == "Poor filtering" and "WHERE" in f.message for f in findings)


def test_no_missing_where_finding_when_where_present() -> None:
    findings = analyze_query("SELECT first_name FROM hr_employees WHERE salary > 1000")
    assert not any("No WHERE clause" in f.message for f in findings)


def test_detects_non_sargable_predicate() -> None:
    findings = analyze_query("SELECT * FROM hr_employees WHERE YEAR(hire_date) = 2024")
    assert any(f.category == "Missing indexes" and "YEAR" in f.message for f in findings)


def test_detects_leading_wildcard_like() -> None:
    findings = analyze_query("SELECT * FROM hr_employees WHERE last_name LIKE '%son'")
    assert any("LIKE" in f.message for f in findings)


def test_detects_implicit_cross_join() -> None:
    sql = (
        "SELECT * FROM hr_employees, hr_departments "
        "WHERE hr_employees.department_id = hr_departments.department_id"
    )
    findings = analyze_query(sql)
    assert any(f.category == "Expensive joins" for f in findings)


def test_no_cross_join_finding_with_explicit_join() -> None:
    sql = "SELECT * FROM hr_employees e JOIN hr_departments d ON e.department_id = d.department_id"
    findings = analyze_query(sql)
    assert not any(f.category == "Expensive joins" for f in findings)


def test_detects_repeated_subquery_with_nested_parens() -> None:
    # The subqueries themselves contain AVG(salary) - a naive regex that
    # stops at the first ')' would mis-parse this and miss the repeat.
    sql = (
        "SELECT * FROM hr_employees WHERE salary > "
        "(SELECT AVG(salary) FROM hr_employees WHERE department_id = 1) "
        "OR salary < (SELECT AVG(salary) FROM hr_employees WHERE department_id = 1) / 2"
    )
    findings = analyze_query(sql)
    assert any(f.category == "Repeated subqueries" for f in findings)


def test_detects_redundant_distinct_with_group_by() -> None:
    findings = analyze_query("SELECT DISTINCT department_id, COUNT(*) FROM hr_employees GROUP BY department_id")
    assert any("DISTINCT" in f.message for f in findings)


def test_clean_query_has_no_findings() -> None:
    sql = "SELECT department_id, AVG(salary) FROM hr_employees WHERE salary > 50000 GROUP BY department_id"
    assert analyze_query(sql) == []
