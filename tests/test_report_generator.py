"""Unit tests for app.core.practice.report_generator. Uses a fake LLM
provider - no network calls, no database connection needed."""

import json

import pytest

from app.core.practice.models import EvaluationResult, GeneratedQuestion, InterviewQuestionRecord
from app.core.practice.report_generator import InterviewReportError, generate_interview_report
from tests.fakes import FakeLLMProvider

_VALID_RESPONSE = json.dumps(
    {
        "strengths": ["Solid grasp of basic SELECT/WHERE filtering.", "Comfortable with GROUP BY aggregation."],
        "weaknesses": ["Struggled with window functions.", "Missed non-sargable predicates."],
        "topics_to_improve": ["Window Functions", "Subqueries"],
        "recommended_learning_path": "1. Review CTEs. 2. Practice ROW_NUMBER/RANK. 3. Retake the interview.",
    }
)


def _make_record(topic: str, difficulty: str, score: int, is_correct: bool, mistakes: tuple = ()) -> InterviewQuestionRecord:
    question = GeneratedQuestion(
        question=f"Sample question about {topic}.",
        topic=topic,
        difficulty=difficulty,
        company="Any / Generic",
        dataset_id="hr",
        relevant_tables=("hr_employees",),
        answer_query="SELECT 1",
    )
    evaluation = EvaluationResult(
        score=score,
        is_correct=is_correct,
        summary="x",
        mistakes=mistakes,
        suggestions=(),
    )
    return InterviewQuestionRecord(question=question, evaluation=evaluation)


def test_generate_report_success_computes_deterministic_stats() -> None:
    records = [
        _make_record("SELECT / WHERE / ORDER BY", "Beginner", 10, True),
        _make_record("Window Functions", "Advanced", 4, False, mistakes=("Wrong PARTITION BY column.",)),
    ]
    llm = FakeLLMProvider(_VALID_RESPONSE)

    report = generate_interview_report(llm, records)

    assert report.total_questions == 2
    assert report.correct_count == 1
    assert report.average_score == 7.0
    assert report.strengths
    assert report.weaknesses
    assert report.topics_to_improve
    assert report.recommended_learning_path


def test_generate_report_requires_all_questions_answered() -> None:
    unanswered = InterviewQuestionRecord(
        question=GeneratedQuestion(
            question="q",
            topic="GROUP BY",
            difficulty="Beginner",
            company="Any / Generic",
            dataset_id="hr",
            relevant_tables=("hr_employees",),
            answer_query="SELECT 1",
        ),
        evaluation=None,
    )
    llm = FakeLLMProvider(_VALID_RESPONSE)

    with pytest.raises(InterviewReportError, match="every question has been answered"):
        generate_interview_report(llm, [unanswered])


def test_generate_report_rejects_malformed_json() -> None:
    records = [_make_record("GROUP BY", "Beginner", 8, True)]
    llm = FakeLLMProvider("not json")

    with pytest.raises(InterviewReportError):
        generate_interview_report(llm, records)


def test_generate_report_rejects_empty_records() -> None:
    llm = FakeLLMProvider(_VALID_RESPONSE)

    with pytest.raises(InterviewReportError):
        generate_interview_report(llm, [])
