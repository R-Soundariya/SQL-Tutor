"""Generates SQL interview practice questions via the configured LLM,
grounded in a real sandbox dataset's schema so the answer query can
actually run against it."""

from __future__ import annotations

import logging

from app.core.db.query_runner import UnsafeQueryError, validate_read_only
from app.core.db.sandbox.loader import get_schema_ddl
from app.core.db.sandbox.schema import DATASETS
from app.core.llm.base import LLMProvider
from app.core.llm.json_utils import LLMResponseParseError, extract_json
from app.core.practice.models import GeneratedQuestion

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior data analyst who writes realistic SQL interview "
    "questions for Data Analyst / Business Analyst / BI Analyst candidates. "
    "You always respond with a single JSON object and nothing else - no "
    "markdown fences, no commentary before or after."
)


class QuestionGenerationError(RuntimeError):
    """Raised when the LLM's generated question/answer can't be used as-is."""


def generate_question(
    llm: LLMProvider,
    dataset_id: str,
    topic: str,
    difficulty: str,
    company: str,
) -> GeneratedQuestion:
    """Ask the LLM for one interview question + canonical answer query,
    grounded in `dataset_id`'s real schema, then validate the answer query
    is safe to execute."""
    if dataset_id not in DATASETS:
        raise ValueError(f"Unknown dataset '{dataset_id}'. Valid options: {list(DATASETS)}")

    dataset = DATASETS[dataset_id]
    schema_ddl = "\n\n".join(get_schema_ddl(dataset_id).values())
    company_line = f" Write it in the style of a {company} interview." if company != "Any / Generic" else ""

    prompt = (
        f"Write one {difficulty}-difficulty SQL interview question about the topic "
        f"'{topic}', answerable against the schema below.{company_line}\n\n"
        f"Schema:\n{schema_ddl}\n\n"
        'Respond with only this JSON shape: {"question": string, "answer_query": string} '
        "where answer_query is a single valid MySQL SELECT (or WITH ... SELECT) "
        "statement using ONLY the exact table and column names given in the schema "
        "above - never invent a table or column."
    )

    raw_response = llm.generate(prompt=prompt, system=_SYSTEM_PROMPT, max_tokens=800, temperature=0.9)

    try:
        parsed = extract_json(raw_response)
        question_text = str(parsed["question"]).strip()
        answer_query = str(parsed["answer_query"]).strip()
    except (LLMResponseParseError, KeyError) as exc:
        logger.warning("Question generation response was unusable: %s", raw_response[:500])
        raise QuestionGenerationError(f"Model response was not usable: {exc}") from exc

    if not question_text or not answer_query:
        raise QuestionGenerationError("Model response was missing a question or answer query.")

    try:
        validate_read_only(answer_query)
    except UnsafeQueryError as exc:
        raise QuestionGenerationError(f"Model produced an unsafe/invalid answer query: {exc}") from exc

    return GeneratedQuestion(
        question=question_text,
        topic=topic,
        difficulty=difficulty,
        company=company,
        dataset_id=dataset_id,
        relevant_tables=tuple(table.name for table in dataset.tables),
        answer_query=answer_query,
    )
