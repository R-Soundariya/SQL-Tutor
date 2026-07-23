"""Difficulty and topic scheduling for the 15-question Mock Interview."""

from __future__ import annotations

from app.core.practice.constants import TOPICS

NUM_QUESTIONS = 15


def difficulty_for_index(index: int) -> str:
    """Beginner for the first third, Intermediate for the middle third,
    Advanced for the last third - a simple, predictable difficulty ramp."""
    if index < 5:
        return "Beginner"
    if index < 10:
        return "Intermediate"
    return "Advanced"


def topic_for_index(index: int) -> str:
    """Cycle through all topics in order so a 15-question interview covers
    as much breadth as possible before any topic repeats."""
    return TOPICS[index % len(TOPICS)]
