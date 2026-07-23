"""Generates three progressively-revealing hints for a practice question,
without handing over a complete working answer.

Deliberately independent of GeneratedQuestion/Lesson: it takes plain
strings so both AI-generated practice questions and hand-authored Learn
SQL lessons can share the same hint behavior.
"""

from __future__ import annotations

import logging
import re

from app.core.llm.base import LLMProvider
from app.core.llm.json_utils import LLMResponseParseError, extract_json

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a patient SQL tutor giving hints to a stuck student. You "
    "never reveal a complete, directly copy-pasteable working query - you "
    "guide the student toward figuring it out themselves. You always "
    "respond with a single JSON object and nothing else."
)


class HintGenerationError(RuntimeError):
    """Raised when the LLM's hint response can't be used as-is."""


def _normalize(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def generate_hints(
    llm: LLMProvider,
    question_text: str,
    schema_ddl: str,
    answer_query: str,
    user_attempt: str = "",
) -> tuple[str, str, str]:
    """Return exactly 3 hints of increasing specificity for `question_text`.

    Hint 1 points at the relevant concept/clause. Hint 2 names the specific
    tables/columns/functions involved. Hint 3 sketches the query's
    structure in plain English, still without runnable SQL. Raises
    HintGenerationError if the model's response is unusable or a hint
    turns out to contain the full answer query verbatim.
    """
    attempt_block = (
        f"\nThe student's current attempt (may be incomplete or wrong):\n{user_attempt}\n"
        if user_attempt.strip()
        else ""
    )

    prompt = (
        f"Question:\n{question_text}\n\n"
        f"Schema:\n{schema_ddl}\n"
        f"{attempt_block}\n"
        "Give exactly 3 hints of increasing specificity to help the student "
        "solve this themselves:\n"
        "- hint_1: point at the general concept/clause needed. No table or column names.\n"
        "- hint_2: name the specific tables, columns, or functions involved. Still no full syntax.\n"
        "- hint_3: sketch the query's structure/steps in plain English (e.g. "
        "'group by X, then filter groups where Y'). Do NOT write a complete, "
        "runnable SQL query in any hint.\n\n"
        'Respond with only this JSON shape: {"hint_1": string, "hint_2": string, "hint_3": string}'
    )

    raw_response = llm.generate(prompt=prompt, system=_SYSTEM_PROMPT, max_tokens=500, temperature=0.5)

    try:
        parsed = extract_json(raw_response)
        hints = (
            str(parsed["hint_1"]).strip(),
            str(parsed["hint_2"]).strip(),
            str(parsed["hint_3"]).strip(),
        )
    except (LLMResponseParseError, KeyError) as exc:
        logger.warning("Hint generation response was unusable: %s", raw_response[:500])
        raise HintGenerationError(f"Model response was not usable: {exc}") from exc

    if any(not hint for hint in hints):
        raise HintGenerationError("Model returned one or more empty hints.")

    normalized_answer = _normalize(answer_query)
    for index, hint in enumerate(hints, start=1):
        if normalized_answer in _normalize(hint):
            raise HintGenerationError(f"Hint {index} appears to contain the full answer query - refusing to show it.")

    return hints
