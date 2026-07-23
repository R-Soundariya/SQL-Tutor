"""Unit tests for app.core.practice.question_generator. Uses a fake LLM
provider - no network calls, no database connection needed."""

import json

import pytest

from app.core.practice.question_generator import QuestionGenerationError, generate_question
from tests.fakes import FakeLLMProvider


def test_generate_question_success() -> None:
    response = json.dumps(
        {
            "question": "Find all employees earning more than 80000.",
            "answer_query": "SELECT first_name, salary FROM hr_employees WHERE salary > 80000",
        }
    )
    llm = FakeLLMProvider(response)

    question = generate_question(
        llm, dataset_id="hr", topic="SELECT / WHERE / ORDER BY", difficulty="Beginner", company="Any / Generic"
    )

    assert "employees" in question.question.lower()
    assert question.dataset_id == "hr"
    assert "hr_employees" in question.relevant_tables


def test_generate_question_rejects_unsafe_answer_query() -> None:
    response = json.dumps(
        {
            "question": "Delete inactive employees.",
            "answer_query": "DELETE FROM hr_employees WHERE salary < 1000",
        }
    )
    llm = FakeLLMProvider(response)

    with pytest.raises(QuestionGenerationError):
        generate_question(
            llm, dataset_id="hr", topic="SELECT / WHERE / ORDER BY", difficulty="Beginner", company="Any / Generic"
        )


def test_generate_question_rejects_malformed_json() -> None:
    llm = FakeLLMProvider("this is not json")

    with pytest.raises(QuestionGenerationError):
        generate_question(llm, dataset_id="hr", topic="GROUP BY", difficulty="Beginner", company="Any / Generic")


def test_generate_question_rejects_unknown_dataset() -> None:
    llm = FakeLLMProvider("{}")

    with pytest.raises(ValueError, match="Unknown dataset"):
        generate_question(
            llm, dataset_id="not_a_real_dataset", topic="GROUP BY", difficulty="Beginner", company="Any / Generic"
        )
