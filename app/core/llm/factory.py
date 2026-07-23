"""Factory that resolves the configured LLMProvider without callers needing
to know which concrete backend (Anthropic, OpenAI, ...) is in use."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.core.llm.anthropic_provider import AnthropicProvider
from app.core.llm.base import LLMProvider
from app.core.llm.openai_provider import OpenAIProvider

_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}


@lru_cache
def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """Instantiate (and cache) the LLMProvider for `provider_name`, defaulting
    to the value of LLM_PROVIDER in settings."""
    settings = get_settings()
    resolved_name = provider_name or settings.llm_provider

    if resolved_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown LLM provider '{resolved_name}'. Valid options: {list(_PROVIDERS)}"
        )

    if resolved_name == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    return OpenAIProvider(settings.openai_api_key, settings.openai_model)
