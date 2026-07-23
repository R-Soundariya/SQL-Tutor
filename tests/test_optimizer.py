"""Unit tests for app.core.optimizer.optimizer. Uses a fake LLM provider -
no network calls, no database connection needed."""

import json

import pytest

from app.core.optimizer.models import StaticFinding
from app.core.optimizer.optimizer import OptimizationError, optimize_query
from tests.fakes import FakeLLMProvider

_VALID_RESPONSE = json.dumps(
    {
        "rewritten_query": "SELECT first_name FROM hr_employees WHERE salary > 80000",
        "performance_notes": "Removed SELECT * to fetch only needed columns.",
        "index_recommendations": ["CREATE INDEX idx_salary ON hr_employees (salary);"],
        "estimated_impact": "Avoids reading unused columns; index enables a range scan instead of a full scan.",
    }
)


def test_optimize_query_success() -> None:
    llm = FakeLLMProvider(_VALID_RESPONSE)

    result = optimize_query(llm, "SELECT * FROM hr_employees WHERE salary > 80000", static_findings=[])

    assert "SELECT first_name" in result.rewritten_query
    assert result.index_recommendations


def test_optimize_query_rejects_non_select_statement() -> None:
    llm = FakeLLMProvider(_VALID_RESPONSE)

    with pytest.raises(OptimizationError, match="read-only"):
        optimize_query(llm, "DELETE FROM hr_employees", static_findings=[])


def test_optimize_query_rejects_malformed_json() -> None:
    llm = FakeLLMProvider("not json")

    with pytest.raises(OptimizationError):
        optimize_query(llm, "SELECT 1", static_findings=[])


def test_optimize_query_rejects_unsafe_rewritten_query() -> None:
    response = json.dumps(
        {
            "rewritten_query": "DROP TABLE hr_employees",
            "performance_notes": "x",
            "index_recommendations": [],
            "estimated_impact": "x",
        }
    )
    llm = FakeLLMProvider(response)

    with pytest.raises(OptimizationError, match="unsafe"):
        optimize_query(llm, "SELECT 1", static_findings=[])


def test_optimize_query_includes_static_findings_in_prompt() -> None:
    captured_prompts: list[str] = []

    class CapturingLLM(FakeLLMProvider):
        def generate(self, prompt, system=None, max_tokens=1024, temperature=0.7):
            captured_prompts.append(prompt)
            return super().generate(prompt, system, max_tokens, temperature)

    llm = CapturingLLM(_VALID_RESPONSE)
    finding = StaticFinding(category="Unnecessary SELECT *", severity="warning", message="Avoid SELECT *.")

    optimize_query(llm, "SELECT * FROM hr_employees", static_findings=[finding])

    assert "Unnecessary SELECT *" in captured_prompts[0]
