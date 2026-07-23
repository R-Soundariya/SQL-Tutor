"""Data models for AI-generated practice questions and their evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedQuestion:
    """One AI-generated interview question, grounded in a sandbox dataset."""

    question: str
    topic: str
    difficulty: str
    company: str
    dataset_id: str
    relevant_tables: tuple[str, ...]
    answer_query: str  # canonical correct SQL, used to compute expected output


@dataclass(frozen=True)
class EvaluationResult:
    """AI-graded feedback on a user's submitted answer."""

    score: int  # 0-10
    is_correct: bool  # from deterministic output comparison, not the LLM's own judgment
    summary: str
    mistakes: tuple[str, ...]
    suggestions: tuple[str, ...]
