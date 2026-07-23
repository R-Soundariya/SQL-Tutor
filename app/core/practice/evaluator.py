"""Grades a user's submitted SQL answer against a generated practice
question, combining a deterministic result-set comparison (ground truth
for correctness) with LLM-generated qualitative feedback (score, mistakes,
suggestions)."""

from __future__ import annotations

import logging

import pandas as pd

from app.core.llm.base import LLMProvider
from app.core.llm.json_utils import LLMResponseParseError, extract_json
from app.core.practice.models import EvaluationResult, GeneratedQuestion

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior data analyst interviewer grading a candidate's SQL "
    "answer. You always respond with a single JSON object and nothing else."
)


class EvaluationError(RuntimeError):
    """Raised when the LLM's evaluation response can't be used as-is."""


def evaluate_answer(
    llm: LLMProvider,
    question: GeneratedQuestion,
    user_query: str,
    user_query_error: str | None,
    user_result: pd.DataFrame | None,
    expected_result: pd.DataFrame,
    outputs_match: bool,
) -> EvaluationResult:
    """Return AI-graded feedback. `outputs_match` (from a deterministic
    comparison the caller already ran) decides `is_correct`; the LLM only
    supplies the score, summary, mistakes, and suggestions."""
    if user_query_error:
        result_description = f"The candidate's query FAILED to execute with this error:\n{user_query_error}"
    else:
        result_description = (
            f"Candidate's query returned {len(user_result)} row(s), columns: {list(user_result.columns)}.\n"
            f"Sample of candidate output (up to 5 rows):\n{user_result.head(5).to_string(index=False)}\n\n"
            f"Expected output (up to 5 rows):\n{expected_result.head(5).to_string(index=False)}\n\n"
            f"Deterministic row-for-row comparison: {'MATCH' if outputs_match else 'NO MATCH'}."
        )

    prompt = (
        f"Interview question ({question.difficulty}, topic: {question.topic}):\n{question.question}\n\n"
        f"Reference/model answer query:\n{question.answer_query}\n\n"
        f"Candidate's submitted query:\n{user_query}\n\n"
        f"{result_description}\n\n"
        "Score the candidate's answer out of 10, treating the deterministic "
        "comparison result as ground truth for whether the output is correct, "
        "and considering query quality/style as a secondary factor. List "
        "concrete mistakes and concrete suggestions for improvement. If the "
        "answer is fully correct, mistakes can be an empty list.\n\n"
        'Respond with only this JSON shape: {"score": integer 0-10, "summary": string, '
        '"mistakes": array of strings, "suggestions": array of strings}'
    )

    raw_response = llm.generate(prompt=prompt, system=_SYSTEM_PROMPT, max_tokens=800, temperature=0.3)

    try:
        parsed = extract_json(raw_response)
        score = int(parsed["score"])
        summary = str(parsed["summary"]).strip()
        mistakes = tuple(str(m) for m in parsed.get("mistakes", []))
        suggestions = tuple(str(s) for s in parsed.get("suggestions", []))
    except (LLMResponseParseError, KeyError, ValueError, TypeError) as exc:
        logger.warning("Evaluation response was unusable: %s", raw_response[:500])
        raise EvaluationError(f"Model response was not usable: {exc}") from exc

    score = max(0, min(10, score))

    return EvaluationResult(
        score=score,
        is_correct=outputs_match,
        summary=summary,
        mistakes=mistakes,
        suggestions=suggestions,
    )
