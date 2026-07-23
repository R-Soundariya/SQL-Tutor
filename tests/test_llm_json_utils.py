"""Unit tests for app.core.llm.json_utils.extract_json."""

import pytest

from app.core.llm.json_utils import LLMResponseParseError, extract_json


def test_extract_plain_json() -> None:
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_with_markdown_fence() -> None:
    text = '```json\n{"a": 1}\n```'
    assert extract_json(text) == {"a": 1}


def test_extract_json_with_surrounding_commentary() -> None:
    text = 'Sure, here you go:\n{"a": 1}\nHope that helps!'
    assert extract_json(text) == {"a": 1}


def test_extract_invalid_json_raises() -> None:
    with pytest.raises(LLMResponseParseError):
        extract_json("not json at all")
