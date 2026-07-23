"""Unit tests for app.core.hints.generator. Uses a fake LLM provider - no
network calls, no database connection needed."""

import json

import pytest

from app.core.hints.generator import HintGenerationError, generate_hints
from tests.fakes import FakeLLMProvider

_SCHEMA = "CREATE TABLE hr_employees (employee_id INT, salary DECIMAL(10,2));"
_ANSWER_QUERY = "SELECT employee_id FROM hr_employees WHERE salary > 80000"


def test_generate_hints_success() -> None:
    response = json.dumps(
        {
            "hint_1": "Think about which clause filters rows.",
            "hint_2": "You'll need the salary column from hr_employees.",
            "hint_3": "Filter rows where salary exceeds the threshold, then select employee_id.",
        }
    )
    llm = FakeLLMProvider(response)

    hints = generate_hints(llm, question_text="Find high earners.", schema_ddl=_SCHEMA, answer_query=_ANSWER_QUERY)

    assert len(hints) == 3
    assert all(hint.strip() for hint in hints)


def test_generate_hints_rejects_malformed_json() -> None:
    llm = FakeLLMProvider("not json")

    with pytest.raises(HintGenerationError):
        generate_hints(llm, question_text="Find high earners.", schema_ddl=_SCHEMA, answer_query=_ANSWER_QUERY)


def test_generate_hints_rejects_empty_hint() -> None:
    response = json.dumps({"hint_1": "Something.", "hint_2": "", "hint_3": "Something else."})
    llm = FakeLLMProvider(response)

    with pytest.raises(HintGenerationError):
        generate_hints(llm, question_text="Find high earners.", schema_ddl=_SCHEMA, answer_query=_ANSWER_QUERY)


def test_generate_hints_rejects_hint_that_leaks_full_answer() -> None:
    response = json.dumps(
        {
            "hint_1": "Think about filtering.",
            "hint_2": "Use the salary column.",
            "hint_3": f"Just run this: {_ANSWER_QUERY}",
        }
    )
    llm = FakeLLMProvider(response)

    with pytest.raises(HintGenerationError, match="appears to contain the full answer query"):
        generate_hints(llm, question_text="Find high earners.", schema_ddl=_SCHEMA, answer_query=_ANSWER_QUERY)
