import json
import os

import httpx

from enrichment.anthropic_client import CATEGORIES, SYSTEM_PROMPT, _unwrap_json
from enrichment.llm import Summary

# Structured Outputs: with strict=true the model is constrained to this schema,
# so the ```json fence the Anthropic path has to strip never appears. Strict mode
# requires additionalProperties=false and every property listed in required.
RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "regwatch_summary",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "category": {"type": "string", "enum": sorted(CATEGORIES)},
                "confidence": {"type": "number"},
            },
            "required": ["summary", "category", "confidence"],
            "additionalProperties": False,
        },
    },
}


class OpenAILLMClient:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-5.4-mini",
        base_url: str = "https://api.openai.com",
        transport: httpx.BaseTransport | None = None,
    ):
        self._api_key = api_key
        self._model = model
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"), transport=transport, timeout=60.0
        )

    @classmethod
    def from_env(cls) -> "OpenAILLMClient":
        try:
            api_key = os.environ["OPENAI_API_KEY"]
        except KeyError as exc:
            raise RuntimeError("OPENAI_API_KEY must be set") from exc
        model = os.environ.get("REGWATCH_OPENAI_MODEL", "gpt-5.4-mini")
        return cls(api_key, model=model)

    def summarize(self, act_text: str, terms: list[str]) -> Summary:
        user = (
            f"Termos monitorados: {', '.join(terms) or '(nenhum)'}.\n\n"
            f"Ato (texto):\n{act_text[:6000]}"
        )
        resp = self._http.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                # max_tokens is rejected by current models; the parameter is
                # max_completion_tokens.
                "max_completion_tokens": 300,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ],
                "response_format": RESPONSE_SCHEMA,
            },
        )
        if resp.is_error:
            raise httpx.HTTPStatusError(
                f"OpenAI refused the request: {resp.status_code} "
                f"{resp.text[:300]} (model={self._model})",
                request=resp.request,
                response=resp,
            )
        try:
            text = _unwrap_json(resp.json()["choices"][0]["message"]["content"])
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
