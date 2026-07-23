"""Generates an aggregate strengths/weaknesses/learning-path report at the
end of a Mock Interview, from the full set of question+evaluation records.

correct_count and average_score are computed deterministically from the
records, the same way EvaluationResult.is_correct is - the LLM only
supplies the qualitative strengths/weaknesses/learning-path narrative.
"""

from __future__ import annotations

import logging

from app.core.llm.base import LLMProvider
from app.core.llm.json_utils import LLMResponseParseError, extract_json
from app.core.practice.models import InterviewQuestionRecord, InterviewReport

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior data analyst who just conducted a mock SQL interview "
    "and is now writing the candidate's feedback report. You always respond "
    "with a single JSON object and nothing else."
)


class InterviewReportError(RuntimeError):
    """Raised when the interview report can't be generated or parsed."""


def generate_interview_report(llm: LLMProvider, records: list[InterviewQuestionRecord]) -> InterviewReport:
    """Summarize a completed Mock Interview into strengths, weaknesses,
    topics to improve, and a recommended learning path."""
    if not records or any(record.evaluation is None for record in records):
        raise InterviewReportError("Cannot generate a report until every question has been answered.")

    total_questions = len(records)
    correct_count = sum(1 for record in records if record.evaluation.is_correct)
    average_score = sum(record.evaluation.score for record in records) / total_questions

    summary_lines = []
    for position, record in enumerate(records, start=1):
        question, evaluation = record.question, record.evaluation
        outcome = "correct" if evaluation.is_correct else "incorrect"
        top_mistake = evaluation.mistakes[0] if evaluation.mistakes else "none noted"
        summary_lines.append(
            f"{position}. [{question.difficulty}/{question.topic}] "
            f"score={evaluation.score}/10, {outcome}, top mistake: {top_mistake}"
        )
    summary_block = "\n".join(summary_lines)

    prompt = (
        f"Candidate completed a {total_questions}-question mock SQL interview. "
        f"Overall: {correct_count}/{total_questions} correct, average score {average_score:.1f}/10.\n\n"
        f"Per-question summary:\n{summary_block}\n\n"
        "Based on this performance, write a feedback report: 3-5 concrete "
        "strengths (topics/skills the candidate clearly handled well), 3-5 "
        "concrete weaknesses (specific gaps, not generic advice), a "
        "prioritized list of topics to improve, and a short recommended "
        "learning path (a few ordered steps) for what to study next.\n\n"
        'Respond with only this JSON shape: {"strengths": [string], '
        '"weaknesses": [string], "topics_to_improve": [string], '
        '"recommended_learning_path": string}'
    )

    raw_response = llm.generate(prompt=prompt, system=_SYSTEM_PROMPT, max_tokens=1200, temperature=0.4)

    try:
        parsed = extract_json(raw_response)
        strengths = tuple(str(item).strip() for item in parsed["strengths"])
        weaknesses = tuple(str(item).strip() for item in parsed["weaknesses"])
        topics_to_improve = tuple(str(item).strip() for item in parsed["topics_to_improve"])
        recommended_learning_path = str(parsed["recommended_learning_path"]).strip()
    except (LLMResponseParseError, KeyError, TypeError) as exc:
        logger.warning("Interview report response was unusable: %s", raw_response[:500])
        raise InterviewReportError(f"Model response was not usable: {exc}") from exc

    return InterviewReport(
        average_score=round(average_score, 2),
        correct_count=correct_count,
        total_questions=total_questions,
        strengths=strengths,
        weaknesses=weaknesses,
        topics_to_improve=topics_to_improve,
        recommended_learning_path=recommended_learning_path,
    )
