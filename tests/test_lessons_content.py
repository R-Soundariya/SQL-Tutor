"""Content-integrity checks for Learn SQL lessons. No database connection
needed - these catch authoring mistakes (typos, wrong table names, unsafe
SQL) before they'd surface as a confusing error in the UI."""

import re

from app.core.db.query_runner import validate_read_only
from app.core.db.sandbox.schema import DATASETS
from app.core.learning.lessons import LESSONS

_TABLE_NAMES_BY_DATASET = {
    dataset_id: {table.name for table in dataset.tables} for dataset_id, dataset in DATASETS.items()
}
_ALL_TABLE_NAMES = {name for names in _TABLE_NAMES_BY_DATASET.values() for name in names}


def _referenced_table_names(sql: str) -> set[str]:
    return {name for name in _ALL_TABLE_NAMES if re.search(rf"\b{name}\b", sql)}


def test_lessons_have_required_fields() -> None:
    for lesson in LESSONS:
        assert lesson.title.strip()
        assert lesson.explanation.strip()
        assert lesson.syntax.strip()
        assert lesson.visual_example.strip()
        assert lesson.practice_question.strip()
        assert lesson.answer_query.strip()
        assert lesson.business_use_case.strip()
        assert len(lesson.common_interview_questions) >= 2


def test_lesson_dataset_id_is_valid() -> None:
    for lesson in LESSONS:
        assert lesson.dataset_id in DATASETS


def test_lesson_answer_query_is_read_only() -> None:
    for lesson in LESSONS:
        validate_read_only(lesson.answer_query)  # should not raise


def test_lesson_answer_query_only_touches_its_own_dataset_tables() -> None:
    for lesson in LESSONS:
        referenced = _referenced_table_names(lesson.answer_query)
        assert referenced, f"{lesson.id}: no known sandbox table referenced"
        own_tables = _TABLE_NAMES_BY_DATASET[lesson.dataset_id]
        assert referenced.issubset(own_tables), (
            f"{lesson.id} references tables outside its own dataset: {referenced - own_tables}"
        )


def test_lesson_ids_are_unique() -> None:
    ids = [lesson.id for lesson in LESSONS]
    assert len(ids) == len(set(ids))
