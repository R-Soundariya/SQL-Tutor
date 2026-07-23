"""Unit tests for Mock Interview difficulty/topic scheduling. Pure
functions - no database or LLM involved."""

from app.core.practice.constants import TOPICS
from app.core.practice.mock_interview import NUM_QUESTIONS, difficulty_for_index, topic_for_index


def test_difficulty_ramps_up_across_thirds() -> None:
    assert difficulty_for_index(0) == "Beginner"
    assert difficulty_for_index(4) == "Beginner"
    assert difficulty_for_index(5) == "Intermediate"
    assert difficulty_for_index(9) == "Intermediate"
    assert difficulty_for_index(10) == "Advanced"
    assert difficulty_for_index(14) == "Advanced"


def test_topic_cycles_through_full_topic_list_without_early_repeats() -> None:
    seen = [topic_for_index(i) for i in range(min(NUM_QUESTIONS, len(TOPICS)))]
    assert len(seen) == len(set(seen))


def test_topic_for_index_wraps_around() -> None:
    assert topic_for_index(0) == topic_for_index(len(TOPICS))


def test_all_scheduled_indices_produce_valid_topics() -> None:
    for i in range(NUM_QUESTIONS):
        assert topic_for_index(i) in TOPICS
