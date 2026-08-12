import logging

import pytest

from enrichment.fallback import FallbackLLMClient
from enrichment.llm import FakeLLMClient, RaisingLLMClient, Summary

PRIMARY = Summary("from primary", "grant", 0.9)
SECONDARY = Summary("from fallback", "tender", 0.8)


def test_uses_the_primary_when_it_succeeds():
    client = FallbackLLMClient(FakeLLMClient(PRIMARY), FakeLLMClient(SECONDARY))
    assert client.summarize("ato", []) == PRIMARY


def test_falls_back_when_the_primary_raises():
    client = FallbackLLMClient(RaisingLLMClient(), FakeLLMClient(SECONDARY))
    assert client.summarize("ato", []) == SECONDARY


def test_logs_a_warning_when_it_falls_back(caplog):
    client = FallbackLLMClient(RaisingLLMClient(), FakeLLMClient(SECONDARY))
    with caplog.at_level(logging.WARNING):
        client.summarize("ato", [])
    assert "falling back" in caplog.text


def test_raises_the_fallbacks_error_when_both_fail():
    client = FallbackLLMClient(RaisingLLMClient(), RaisingLLMClient())
    with pytest.raises(RuntimeError):
        client.summarize("ato", [])


def test_raises_the_primary_error_when_there_is_no_fallback():
    client = FallbackLLMClient(RaisingLLMClient(), None)
    with pytest.raises(RuntimeError):
        client.summarize("ato", [])


def test_from_env_degrades_to_primary_only_when_the_fallback_key_is_absent(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    client = FallbackLLMClient.from_env()

    assert client._fallback is None, "a missing second key must not break the run"


def test_from_env_promotes_the_fallback_when_the_primary_key_is_absent(monkeypatch):
    """A missing primary key must degrade, not kill the run.

    OPENAI_API_KEY was absent from the Cloud Run job on 2026-08-12 and the
    unguarded primary construction would have raised straight out of
    get_llm_client(), failing the whole daily run — including the scrape,
    matching and digest delivery that need no LLM at all.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic")

    client = FallbackLLMClient.from_env()

    from enrichment.anthropic_client import AnthropicLLMClient
    assert isinstance(client._primary, AnthropicLLMClient)
    assert client._fallback is None
    assert client.summarize.__self__ is client  # still a usable LLMClient


def test_from_env_raises_when_neither_provider_is_configured(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="no usable LLM provider"):
        FallbackLLMClient.from_env()
