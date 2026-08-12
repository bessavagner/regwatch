import json

import httpx
import pytest

from enrichment.llm import Summary
from enrichment.openai_client import OpenAILLMClient


def _chat_response(text: str) -> httpx.Response:
    # Shape of an OpenAI Chat Completions success body.
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def test_summarize_parses_model_json_into_summary():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = request.headers
        captured["body"] = json.loads(request.content)
        return _chat_response(json.dumps(
            {"summary": "Concede licença à Beta Corp.", "category": "grant", "confidence": 0.9}
        ))

    client = OpenAILLMClient("sk-test", transport=httpx.MockTransport(handler))
    result = client.summarize("Licença concedida à BETA CORP.", ["beta corp"])

    assert isinstance(result, Summary)
    assert result.summary == "Concede licença à Beta Corp."
    assert result.category == "grant"
    assert result.confidence == 0.9
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["headers"].get("authorization") == "Bearer sk-test"
    assert captured["body"]["model"] == "gpt-5.6-luna"
    # Newer OpenAI models reject max_tokens.
    assert "max_tokens" not in captured["body"]
    assert captured["body"]["max_completion_tokens"] == 300


def test_summarize_asks_for_a_strict_json_schema():
    def handler(request):
        body = json.loads(request.content)
        fmt = body["response_format"]
        assert fmt["type"] == "json_schema"
        assert fmt["json_schema"]["strict"] is True
        assert fmt["json_schema"]["schema"]["additionalProperties"] is False
        return _chat_response(json.dumps(
            {"summary": "s", "category": "other", "confidence": 0.5}
        ))

    OpenAILLMClient("sk-test", transport=httpx.MockTransport(handler)).summarize("ato", [])


def test_unknown_category_falls_back_to_other():
    def handler(request):
        return _chat_response(json.dumps(
            {"summary": "s", "category": "licitação", "confidence": 0.5}
        ))

    result = OpenAILLMClient("sk-test", transport=httpx.MockTransport(handler)).summarize("a", [])
    assert result.category == "other"


def test_confidence_is_clamped_into_range():
    def handler(request):
        return _chat_response(json.dumps(
            {"summary": "s", "category": "grant", "confidence": 4.2}
        ))

    result = OpenAILLMClient("sk-test", transport=httpx.MockTransport(handler)).summarize("a", [])
    assert result.confidence == 1.0


def test_unparseable_reply_raises_value_error():
    def handler(request):
        return _chat_response("not json at all")

    client = OpenAILLMClient("sk-test", transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        client.summarize("a", [])


def test_error_status_reports_the_providers_explanation():
    def handler(request):
        return httpx.Response(429, json={"error": {"message": "insufficient_quota"}})

    client = OpenAILLMClient("sk-secret-value", transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        client.summarize("a", [])

    message = str(excinfo.value)
    assert "insufficient_quota" in message
    assert "sk-secret-value" not in message


def test_from_env_reads_key_and_optional_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.setenv("REGWATCH_OPENAI_MODEL", "gpt-5.6-terra")
    client = OpenAILLMClient.from_env()
    assert client._api_key == "sk-env"
    assert client._model == "gpt-5.6-terra"


def test_from_env_defaults_to_the_cost_tier(monkeypatch):
    # The model name is a moving target; the default must stay the cheap tier
    # rather than drifting onto a flagship at 25x the input price.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.delenv("REGWATCH_OPENAI_MODEL", raising=False)
    assert OpenAILLMClient.from_env()._model == "gpt-5.6-luna"


def test_from_env_raises_when_key_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        OpenAILLMClient.from_env()


def test_act_text_is_truncated_before_sending():
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return _chat_response(json.dumps(
            {"summary": "s", "category": "other", "confidence": 0.5}
        ))

    client = OpenAILLMClient("sk-test", transport=httpx.MockTransport(handler))
    client.summarize("x" * 20000, [])
    assert len(captured["body"]["messages"][1]["content"]) < 7000
