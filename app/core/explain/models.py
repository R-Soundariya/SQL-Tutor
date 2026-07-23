"""Data model for an AI-generated SQL query explanation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClauseExplanation:
    """Plain-English explanation of one clause present in the query."""

    clause: str
    explanation: str


@dataclass(frozen=True)
class ExplanationResult:
    """Full breakdown of a single explained query."""

    clauses: tuple[ClauseExplanation, ...]
    execution_order: tuple[str, ...]
    business_meaning: str
    output_description: str
    complexity_notes: str
