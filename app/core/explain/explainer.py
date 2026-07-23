"""Explains a SQL query via the configured LLM: what each clause does, the
logical execution order, likely business meaning, expected output, and
brief complexity/performance notes.

Complexity notes here are deliberately lightweight/descriptive - deep
index and rewrite recommendations belong to the dedicated Query Optimizer
feature, not this one.
"""

from __future__ import annotations

import logging

from app.core.db.query_runner import UnsafeQueryError, validate_read_only
from app.core.explain.models import ClauseExplanation, ExplanationResult
from app.core.llm.base import LLMProvider
from app.core.llm.json_utils import LLMResponseParseError, extract_json

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior data analyst explaining a SQL query to someone "
    "learning SQL. You always respond with a single JSON object and "
    "nothing else - no markdown fences, no commentary before or after."
)


class ExplanationError(RuntimeError):
    """Raised when the query can't be explained or the LLM response is unusable."""


def explain_query(llm: LLMProvider, sql: str, schema_ddl: str | None = None) -> ExplanationResult:
    """Validate `sql` is a safe read-only statement, then ask the LLM to
    explain it. `schema_ddl`, if given, grounds the explanation in real
    table/column context; otherwise the model infers meaning from the SQL
    text and naming alone."""
    try:
        validate_read_only(sql)
    except UnsafeQueryError as exc:
        raise ExplanationError(f"Only a single read-only SELECT/WITH statement can be explained: {exc}") from exc

    schema_block = f"Schema for context:\n{schema_ddl}\n\n" if schema_ddl else ""

    prompt = (
        f"{schema_block}"
        f"Explain this SQL query:\n{sql}\n\n"
        "Break it down clause by clause - only the clauses actually present "
        "in the query (e.g. skip HAVING if there's none). For each clause, "
        "give a short plain-English explanation of what it does in THIS "
        "query specifically.\n\n"
        "Then describe the logical execution order (the order the database "
        "actually evaluates clauses in - FROM/JOIN, WHERE, GROUP BY, HAVING, "
        "SELECT, DISTINCT, ORDER BY, LIMIT - listing only the steps that "
        "apply here), the likely business meaning of running this query, "
        "what the output would look like (columns, rough shape), and brief "
        "complexity/performance notes (e.g. join cost, whether an index "
        "would help, subquery/CTE re-evaluation concerns).\n\n"
        'Respond with only this JSON shape: {"clauses": [{"clause": string, '
        '"explanation": string}], "execution_order": [string], '
        '"business_meaning": string, "output_description": string, '
        '"complexity_notes": string}'
    )

    raw_response = llm.generate(prompt=prompt, system=_SYSTEM_PROMPT, max_tokens=1200, temperature=0.4)

    try:
        parsed = extract_json(raw_response)
        clauses = tuple(
            ClauseExplanation(clause=str(item["clause"]).strip(), explanation=str(item["explanation"]).strip())
            for item in parsed["clauses"]
        )
        execution_order = tuple(str(step).strip() for step in parsed["execution_order"])
        business_meaning = str(parsed["business_meaning"]).strip()
        output_description = str(parsed["output_description"]).strip()
        complexity_notes = str(parsed["complexity_notes"]).strip()
    except (LLMResponseParseError, KeyError, TypeError) as exc:
        logger.warning("Explain response was unusable: %s", raw_response[:500])
        raise ExplanationError(f"Model response was not usable: {exc}") from exc

    if not clauses:
        raise ExplanationError("Model did not return any clause breakdown.")

    return ExplanationResult(
        clauses=clauses,
        execution_order=execution_order,
        business_meaning=business_meaning,
        output_description=output_description,
        complexity_notes=complexity_notes,
    )
