"""Deterministic, LLM-free static checks for common SQL anti-patterns.

Runs on the raw SQL text - no database connection and no API call needed -
so these findings are always available immediately, before (or even
without) any AI call.
"""

from __future__ import annotations

import re

from app.core.optimizer.models import StaticFinding

_NON_SARGABLE_FUNCTIONS = ("YEAR", "MONTH", "DAY", "UPPER", "LOWER", "DATE", "CAST", "SUBSTRING", "TRIM")


def _find_where_clause(sql: str) -> str | None:
    match = re.search(
        r"\bWHERE\b(.*?)(\bGROUP BY\b|\bHAVING\b|\bORDER BY\b|\bLIMIT\b|$)", sql, re.IGNORECASE | re.DOTALL
    )
    return match.group(1) if match else None


def _extract_parenthesized_selects(sql: str) -> list[str]:
    """Find every balanced-paren span whose content starts with SELECT,
    using explicit paren matching (a regex can't handle nesting - e.g. a
    subquery containing COUNT(*) would otherwise close on the wrong paren)."""
    subqueries: list[str] = []
    open_positions: list[int] = []
    for index, char in enumerate(sql):
        if char == "(":
            open_positions.append(index)
        elif char == ")" and open_positions:
            start = open_positions.pop()
            inner = sql[start + 1 : index]
            if re.match(r"\s*SELECT\b", inner, re.IGNORECASE):
                subqueries.append(inner)
    return subqueries


def _find_repeated_subqueries(sql: str) -> list[str]:
    normalized = [re.sub(r"\s+", " ", s.strip().lower()) for s in _extract_parenthesized_selects(sql)]
    seen: set[str] = set()
    repeated: list[str] = []
    for text in normalized:
        if normalized.count(text) > 1 and text not in seen:
            repeated.append(text)
            seen.add(text)
    return repeated


def analyze_query(sql: str) -> list[StaticFinding]:
    """Run every static check against `sql` and return the findings."""
    findings: list[StaticFinding] = []

    if re.search(r"SELECT\s+\*", sql, re.IGNORECASE):
        findings.append(
            StaticFinding(
                category="Unnecessary SELECT *",
                severity="warning",
                message=(
                    "SELECT * fetches every column, including ones you may not need, wasting I/O "
                    "and bandwidth, and can silently break if the table's columns change. List only "
                    "the columns you actually use."
                ),
            )
        )

    if re.search(r"\bFROM\b", sql, re.IGNORECASE) and not re.search(r"\bWHERE\b", sql, re.IGNORECASE):
        findings.append(
            StaticFinding(
                category="Poor filtering",
                severity="warning",
                message=(
                    "No WHERE clause was found - this query will scan every row in the table(s). "
                    "Add a filter if you don't actually need the full table."
                ),
            )
        )

    where_clause = _find_where_clause(sql)
    if where_clause:
        for function_name in _NON_SARGABLE_FUNCTIONS:
            if re.search(rf"\b{function_name}\s*\(", where_clause, re.IGNORECASE):
                findings.append(
                    StaticFinding(
                        category="Missing indexes",
                        severity="warning",
                        message=(
                            f"WHERE clause wraps a column in {function_name}(...), which prevents MySQL "
                            "from using a normal index on that column (a non-sargable predicate). "
                            "Consider rewriting to compare the raw column instead."
                        ),
                    )
                )
                break

        if re.search(r"LIKE\s+'%", where_clause, re.IGNORECASE):
            findings.append(
                StaticFinding(
                    category="Missing indexes",
                    severity="warning",
                    message=(
                        "A LIKE pattern starting with '%' can't use a standard B-tree index, forcing a "
                        "full scan. Consider a full-text index or restructuring the search."
                    ),
                )
            )

    if re.search(r"FROM\s+\w+(\s*,\s*\w+)+", sql, re.IGNORECASE) and not re.search(r"\bJOIN\b", sql, re.IGNORECASE):
        findings.append(
            StaticFinding(
                category="Expensive joins",
                severity="critical",
                message=(
                    "Comma-separated tables in FROM without an explicit JOIN risk an accidental cross "
                    "join (every row matched with every row). Use explicit JOIN ... ON syntax instead."
                ),
            )
        )

    repeated_subqueries = _find_repeated_subqueries(sql)
    if repeated_subqueries:
        findings.append(
            StaticFinding(
                category="Repeated subqueries",
                severity="warning",
                message=(
                    f"The same subquery pattern appears more than once ({len(repeated_subqueries)} distinct "
                    "repeated pattern(s)). MySQL may re-evaluate it each time - consider a CTE (WITH ...) "
                    "to compute it once and reuse it."
                ),
            )
        )

    if re.search(r"\bDISTINCT\b", sql, re.IGNORECASE) and re.search(r"\bGROUP BY\b", sql, re.IGNORECASE):
        findings.append(
            StaticFinding(
                category="Poor filtering",
                severity="info",
                message=(
                    "DISTINCT combined with GROUP BY is usually redundant - GROUP BY already collapses "
                    "duplicate groups. Double-check whether you need both."
                ),
            )
        )

    return findings
