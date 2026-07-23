"""Provider-agnostic LLM interface used throughout the app."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Common interface every LLM backend (Anthropic, OpenAI, ...) must implement."""

    name: str

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Send a prompt to the LLM and return its text response.

        Args:
            prompt: The user-turn content (question, query to explain, etc.).
            system: Optional system instruction steering the model's behavior/role.
            max_tokens: Upper bound on response length.
            temperature: Sampling temperature; lower = more deterministic.

        Returns:
            The model's text response.
        """
        raise NotImplementedError
