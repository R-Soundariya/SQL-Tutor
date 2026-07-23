"""Data model for a single Learn SQL lesson."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lesson:
    """One self-contained SQL concept lesson."""

    id: str
    title: str
    category: str
    difficulty: str  # "Beginner" | "Intermediate" | "Advanced"
    explanation: str  # markdown
    syntax: str  # SQL code block content
    visual_example: str  # markdown, a small hand-built before/after illustration
    dataset_id: str  # key into app.core.db.sandbox.schema.DATASETS
    practice_question: str
    answer_query: str  # canonical correct SQL, used to compute expected output
    business_use_case: str
    common_interview_questions: tuple[str, ...]
