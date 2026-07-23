"""AI-assisted query optimization: combines deterministic static findings
(and, when available, a real MySQL EXPLAIN plan) with an LLM-generated
rewrite, index recommendations, and performance notes."""

from __future__ import annotations

import logging

from app.core.db.query_runner import UnsafeQueryError, validate_read_only
from app.core.llm.base import LLMProvider
from app.core.llm.json_utils import LLMResponseParseError, extract_json
from app.core.optimizer.models import OptimizationResult, StaticFinding

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior data analyst who specializes in SQL performance "
    "tuning for MySQL. You always respond with a single JSON object and "
    "nothing else - no markdown fences, no commentary before or after."
)


class OptimizationError(RuntimeError):
    """Raised when the query can't be optimized or the LLM response is unusable."""


def optimize_query(
    llm: LLMProvider,
    sql: str,
    static_findings: list[StaticFinding],
    schema_ddl: str | None = None,
    explain_plan_text: str | None = None,
) -> OptimizationResult:
    """Ask the LLM for a rewritten query and recommendations, building on
    `static_findings` (already computed, no LLM needed) and an optional
    real EXPLAIN plan for grounding."""
    try:
        validate_read_only(sql)
    except UnsafeQueryError as exc:
        raise OptimizationError(f"Only a single read-only SELECT/WITH statement can be optimized: {exc}") from exc

    schema_block = f"Schema for context:\n{schema_ddl}\n\n" if schema_ddl else ""
    explain_block = f"MySQL's real EXPLAIN plan for this query:\n{explain_plan_text}\n\n" if explain_plan_text else ""
    findings_block = (
        "Static analysis already found these issues:\n"
        + "\n".join(f"- [{finding.category}] {finding.message}" for finding in static_findings)
        + "\n\n"
        if static_findings
        else "Static analysis found no obvious issues.\n\n"
    )

    prompt = (
        f"{schema_block}{explain_block}{findings_block}"
        f"Query to optimize:\n{sql}\n\n"
        "Analyze this query for performance issues (poor filtering, unnecessary "
        "SELECT *, missing indexes, expensive joins, repeated subqueries), building "
        "on the static findings above rather than repeating them verbatim. Then "
        "produce: a rewritten, optimized query that is semantically equivalent "
        "(returns the same results); a short performance notes paragraph explaining "
        "what changed and why; a list of concrete index recommendations (as CREATE "
        "INDEX statements where possible); and a short, honest estimate of the "
        "expected performance improvement (qualitative is fine, e.g. 'avoids a full "
        "table scan on orders').\n\n"
        'Respond with only this JSON shape: {"rewritten_query": string, '
        '"performance_notes": string, "index_recommendations": [string], '
        '"estimated_impact": string}'
    )

    raw_response = llm.generate(prompt=prompt, system=_SYSTEM_PROMPT, max_tokens=1200, temperature=0.3)

    try:
        parsed = extract_json(raw_response)
        rewritten_query = str(parsed["rewritten_query"]).strip()
        performance_notes = str(parsed["performance_notes"]).strip()
        index_recommendations = tuple(str(item).strip() for item in parsed.get("index_recommendations", []))
        estimated_impact = str(parsed["estimated_impact"]).strip()
    except (LLMResponseParseError, KeyError, TypeError) as exc:
        logger.warning("Optimization response was unusable: %s", raw_response[:500])
        raise OptimizationError(f"Model response was not usable: {exc}") from exc

    if not rewritten_query:
        raise OptimizationError("Model did not return a rewritten query.")

    try:
        validate_read_only(rewritten_query)
    except UnsafeQueryError as exc:
        raise OptimizationError(f"Model produced an unsafe rewritten query: {exc}") from exc

    return OptimizationResult(
        rewritten_query=rewritten_query,
        performance_notes=performance_notes,
        index_recommendations=index_recommendations,
        estimated_impact=estimated_impact,
    )
