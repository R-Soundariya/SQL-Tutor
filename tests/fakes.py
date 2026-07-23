"""Test doubles shared across the test suite."""

from __future__ import annotations

from app.core.llm.base import LLMProvider


class FakeLLMProvider(LLMProvider):
    """Returns a fixed canned response instead of calling a real API."""

    name = "fake"

    def __init__(self, response: str) -> None:
        self._response = response

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        return self._response
