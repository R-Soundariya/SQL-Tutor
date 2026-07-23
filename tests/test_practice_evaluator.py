"""Unit tests for app.core.practice.evaluator. Uses a fake LLM provider and
in-memory DataFrames - no network calls, no database connection needed."""

import json

import pandas as pd
import pytest

from app.core.practice.evaluator import EvaluationError, evaluate_answer
from app.core.practice.models import GeneratedQuestion
from tests.fakes import FakeLLMProvider


def _sample_question() -> GeneratedQuestion:
    return GeneratedQuestion(
        question="Find employees earning more than 80000.",
        topic="SELECT / WHERE / ORDER BY",
        difficulty="Beginner",
        company="Any / Generic",
        dataset_id="hr",
        relevant_tables=("hr_employees",),
        answer_query="SELECT first_name FROM hr_employees WHERE salary > 80000",
    )


def test_evaluate_correct_answer() -> None:
    response = json.dumps(
        {
            "score": 10,
            "summary": "Great job, fully correct.",
            "mistakes": [],
            "suggestions": ["Consider adding a column alias."],
        }
    )
    llm = FakeLLMProvider(response)
    expected_df = pd.DataFrame({"first_name": ["Asha"]})
    user_df = pd.DataFrame({"first_name": ["Asha"]})

    result = evaluate_answer(
        llm=llm,
        question=_sample_question(),
        user_query="SELECT first_name FROM hr_employees WHERE salary > 80000",
        user_query_error=None,
        user_result=user_df,
        expected_result=expected_df,
        outputs_match=True,
    )

    assert result.is_correct is True
    assert result.score == 10
    assert result.mistakes == ()


def test_evaluate_clamps_out_of_range_score() -> None:
    response = json.dumps({"score": 15, "summary": "x", "mistakes": [], "suggestions": []})
    llm = FakeLLMProvider(response)
    df = pd.DataFrame({"a": [1]})

    result = evaluate_answer(
        llm=llm,
        question=_sample_question(),
        user_query="SELECT 1",
        user_query_error=None,
        user_result=df,
        expected_result=df,
        outputs_match=True,
    )

    assert result.score == 10


def test_evaluate_uses_deterministic_match_for_is_correct_not_llm_opinion() -> None:
    # Even if the LLM were to imply correctness in its summary, is_correct
    # must come from the caller-supplied outputs_match flag.
    response = json.dumps({"score": 9, "summary": "Looks right to me!", "mistakes": [], "suggestions": []})
    llm = FakeLLMProvider(response)
    df = pd.DataFrame({"a": [1]})

    result = evaluate_answer(
        llm=llm,
        question=_sample_question(),
        user_query="SELECT 1",
        user_query_error=None,
        user_result=df,
        expected_result=df,
        outputs_match=False,
    )

    assert result.is_correct is False


def test_evaluate_handles_query_execution_error() -> None:
    response = json.dumps(
        {"score": 2, "summary": "Query failed.", "mistakes": ["Syntax error"], "suggestions": ["Check column names."]}
    )
    llm = FakeLLMProvider(response)
    expected_df = pd.DataFrame({"a": [1]})

    result = evaluate_answer(
        llm=llm,
        question=_sample_question(),
        user_query="SELEKT 1",
        user_query_error="syntax error near SELEKT",
        user_result=None,
        expected_result=expected_df,
        outputs_match=False,
    )

    assert result.is_correct is False
    assert result.score == 2


def test_evaluate_rejects_malformed_json() -> None:
    llm = FakeLLMProvider("not json")
    df = pd.DataFrame({"a": [1]})

    with pytest.raises(EvaluationError):
        evaluate_answer(
            llm=llm,
            question=_sample_question(),
            user_query="SELECT 1",
            user_query_error=None,
            user_result=df,
            expected_result=df,
            outputs_match=True,
        )
