"""Two providers behind one LLMClient.

Enrichment was dead from 2026-07-24 to 2026-08-07 because a single provider
returned 400 on every call and enrich_match swallows the failure. One provider
is a single point of failure for the only part of the digest a reader actually
reads.
"""
import logging
import os

from django.utils.module_loading import import_string

from enrichment.llm import LLMClient, Summary

logger = logging.getLogger(__name__)

DEFAULT_PRIMARY = "enrichment.openai_client.OpenAILLMClient"
DEFAULT_FALLBACK = "enrichment.anthropic_client.AnthropicLLMClient"


class FallbackLLMClient:
    def __init__(self, primary: LLMClient, fallback: LLMClient | None):
        self._primary = primary
        self._fallback = fallback

    @classmethod
    def from_env(cls) -> "FallbackLLMClient":
        primary_path = os.environ.get("REGWATCH_LLM_PRIMARY", DEFAULT_PRIMARY)
        fallback_path = os.environ.get("REGWATCH_LLM_FALLBACK", DEFAULT_FALLBACK)

        primary = import_string(primary_path).from_env()
        try:
            fallback = import_string(fallback_path).from_env()
        except Exception:
            # A missing or misconfigured second key degrades the run to
            # primary-only; it must never stop the day's digests going out.
            logger.warning("no usable fallback LLM (%s); running primary-only", fallback_path)
            fallback = None
        return cls(primary, fallback)

    def summarize(self, act_text: str, terms: list[str]) -> Summary:
        try:
            return self._primary.summarize(act_text, terms)
        except Exception:
            if self._fallback is None:
                raise
            logger.warning(
                "primary LLM failed, falling back to the secondary provider",
                exc_info=True,
            )
        return self._fallback.summarize(act_text, terms)
