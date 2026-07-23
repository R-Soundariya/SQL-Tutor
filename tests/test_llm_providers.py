"""Unit tests for the LLM provider abstraction. No real API calls are made -
provider constructors only build a client object, they don't hit the network."""

import pytest

from app.core.llm.anthropic_provider import AnthropicProvider
from app.core.llm.base import LLMProvider
from app.core.llm.factory import get_llm_provider
from app.core.llm.openai_provider import OpenAIProvider


def test_anthropic_provider_requires_api_key() -> None:
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        AnthropicProvider(api_key="", model="claude-sonnet-5")


def test_openai_provider_requires_api_key() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIProvider(api_key="", model="gpt-4o-mini")


def test_providers_implement_common_interface() -> None:
    anthropic_provider = AnthropicProvider(api_key="fake-key", model="claude-sonnet-5")
    openai_provider = OpenAIProvider(api_key="fake-key", model="gpt-4o-mini")

    assert isinstance(anthropic_provider, LLMProvider)
    assert isinstance(openai_provider, LLMProvider)
    assert anthropic_provider.name == "anthropic"
    assert openai_provider.name == "openai"


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm_provider("not-a-real-provider")
