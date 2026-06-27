import json
import os

import httpx

from enrichment.llm import Summary

CATEGORIES = {"grant", "penalty", "appointment", "tender", "regulation", "other"}

SYSTEM_PROMPT = (
    "Você resume atos do Diário Oficial da União para um sistema de monitoramento. "
    "Responda SOMENTE com um objeto JSON com as chaves: "
    '"summary" (uma frase em português), '
    '"category" (um de: grant, penalty, appointment, tender, regulation, other) e '
    '"confidence" (número entre 0 e 1). Sem texto fora do JSON.'
)


class AnthropicLLMClient:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "claude-haiku-4-5-20251001",
        base_url: str = "https://api.anthropic.com",
        transport: httpx.BaseTransport | None = None,
    ):
        self._api_key = api_key
        self._model = model
        self._http = httpx.Client(base_url=base_url.rstrip("/"), transport=transport, timeout=60.0)

    @classmethod
    def from_env(cls) -> "AnthropicLLMClient":
        try:
            api_key = os.environ["ANTHROPIC_API_KEY"]
        except KeyError as exc:
            raise RuntimeError("ANTHROPIC_API_KEY must be set") from exc
        model = os.environ.get("REGWATCH_LLM_MODEL", "claude-haiku-4-5-20251001")
        return cls(api_key, model=model)

    def summarize(self, act_text: str, terms: list[str]) -> Summary:
        user = (
            f"Termos monitorados: {', '.join(terms) or '(nenhum)'}.\n\n"
            f"Ato (texto):\n{act_text[:6000]}"
        )
        resp = self._http.post(
            "/v1/messages",
            headers={"x-api-key": self._api_key, "anthropic-version": "2023-06-01"},
            json={
                "model": self._model,
                "max_tokens": 300,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user}],
            },
        )
        resp.raise_for_status()
        try:
            text = resp.json()["content"][0]["text"]
            data = json.loads(text)
            summary = str(data["summary"])
            category = str(data["category"])
            confidence = float(data["confidence"])
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ValueError("could not parse LLM reply into Summary") from exc

        if category not in CATEGORIES:
            category = "other"
        confidence = max(0.0, min(1.0, confidence))
        return Summary(summary=summary, category=category, confidence=confidence)
