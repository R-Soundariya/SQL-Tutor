"""Unit tests for app.core.explain.explainer. Uses a fake LLM provider - no
network calls, no database connection needed."""

import json

import pytest

from app.core.explain.explainer import ExplanationError, explain_query
from tests.fakes import FakeLLMProvider

_VALID_RESPONSE = json.dumps(
    {
        "clauses": [
            {"clause": "SELECT department_id, AVG(salary)", "explanation": "Returns department and average salary."},
            {"clause": "FROM hr_employees", "explanation": "Reads from the employees table."},
            {"clause": "GROUP BY department_id", "explanation": "Collapses rows into one per department."},
        ],
        "execution_order": ["FROM hr_employees", "GROUP BY department_id", "SELECT department_id, AVG(salary)"],
        "business_meaning": "Finds average pay per department.",
        "output_description": "One row per department with its average salary.",
        "complexity_notes": "Single table aggregation, cheap unless department_id is unindexed.",
    }
)


def test_explain_query_success() -> None:
    llm = FakeLLMProvider(_VALID_RESPONSE)

    result = explain_query(llm, "SELECT department_id, AVG(salary) FROM hr_employees GROUP BY department_id")

    assert len(result.clauses) == 3
    assert result.clauses[0].clause == "SELECT department_id, AVG(salary)"
    assert len(result.execution_order) == 3
    assert result.business_meaning
    assert result.output_description
    assert result.complexity_notes


def test_explain_query_rejects_non_select_statement() -> None:
    llm = FakeLLMProvider(_VALID_RESPONSE)

    with pytest.raises(ExplanationError, match="read-only"):
        explain_query(llm, "DROP TABLE hr_employees")


def test_explain_query_rejects_malformed_json() -> None:
    llm = FakeLLMProvider("not json")

    with pytest.raises(ExplanationError):
        explain_query(llm, "SELECT 1")


def test_explain_query_rejects_empty_clause_list() -> None:
    response = json.dumps(
        {
            "clauses": [],
            "execution_order": [],
            "business_meaning": "x",
            "output_description": "x",
            "complexity_notes": "x",
        }
    )
    llm = FakeLLMProvider(response)

    with pytest.raises(ExplanationError, match="clause breakdown"):
        explain_query(llm, "SELECT 1")
