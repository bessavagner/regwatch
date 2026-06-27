import json

import httpx
import pytest

from enrichment.anthropic_client import AnthropicLLMClient
from enrichment.llm import Summary


def _messages_response(text: str) -> httpx.Response:
    # Shape of an Anthropic Messages API success body.
    return httpx.Response(200, json={"content": [{"type": "text", "text": text}]})


def test_summarize_parses_model_json_into_summary():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = request.headers
        captured["body"] = json.loads(request.content)
        reply = json.dumps(
            {"summary": "Concede licença à Beta Corp.", "category": "grant", "confidence": 0.9}
        )
        return _messages_response(reply)

    client = AnthropicLLMClient("sk-test", transport=httpx.MockTransport(handler))
    result = client.summarize("Licença concedida à BETA CORP.", ["beta corp"])

    assert isinstance(result, Summary)
    assert result.summary == "Concede licença à Beta Corp."
    assert result.category == "grant"
    assert result.confidence == 0.9
    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["headers"].get("x-api-key") == "sk-test"
    assert captured["headers"].get("anthropic-version")
    assert captured["body"]["model"] == "claude-haiku-4-5-20251001"


def test_summarize_coerces_unknown_category_to_other():
    def handler(request):
        reply = json.dumps({"summary": "x", "category": "banana", "confidence": 2})
        return _messages_response(reply)

    client = AnthropicLLMClient("k", transport=httpx.MockTransport(handler))
    result = client.summarize("text", [])
    assert result.category == "other"      # not in taxonomy -> other
    assert result.confidence == 1.0        # clamped to [0, 1]


def test_summarize_raises_on_unparseable_reply():
    def handler(request):
        return _messages_response("not json at all")

    client = AnthropicLLMClient("k", transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        client.summarize("text", [])


def test_from_env_reads_key_and_optional_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-env")
    monkeypatch.setenv("REGWATCH_LLM_MODEL", "claude-test-model")
    client = AnthropicLLMClient.from_env()
    assert client._api_key == "sk-env"
    assert client._model == "claude-test-model"


def test_from_env_raises_when_key_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        AnthropicLLMClient.from_env()
