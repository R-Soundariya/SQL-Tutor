"""Helpers for parsing structured JSON out of LLM responses.

Models are instructed to respond with JSON only, but reliably still wrap it
in markdown fences or add a sentence of commentary - this tolerates both.
"""

from __future__ import annotations

import json
import re


class LLMResponseParseError(ValueError):
    """Raised when an LLM response could not be parsed as the expected JSON."""


def extract_json(text: str) -> dict:
    """Parse a single JSON object out of an LLM response."""
    candidate = text.strip()

    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if brace_match:
            candidate = brace_match.group(0)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise LLMResponseParseError(
            f"Could not parse JSON from LLM response: {exc}\nRaw response: {text[:500]}"
        ) from exc
