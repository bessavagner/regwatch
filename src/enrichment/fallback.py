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

        # Both constructions are guarded, and symmetrically. A provider whose
        # key is absent is a configuration gap, not a reason to lose the day:
        # enrichment is one step of run_daily, and the scrape, matching and
        # digest delivery around it need no LLM at all. Only having *neither*
        # provider is fatal.
        primary = cls._build(primary_path)
        fallback = cls._build(fallback_path)

        if primary is None:
            if fallback is None:
                raise RuntimeError(
                    f"no usable LLM provider: neither {primary_path} nor "
                    f"{fallback_path} could be constructed from the environment"
                )
            # Promote, so summarize() always has a primary to call and the
            # single-provider path stays the same shape as the two-provider one.
            logger.warning(
                "primary LLM %s unavailable; promoting %s and running single-provider",
                primary_path, fallback_path,
            )
            return cls(fallback, None)

        if fallback is None:
            logger.warning("no usable fallback LLM (%s); running primary-only", fallback_path)
        return cls(primary, fallback)

    @staticmethod
    def _build(path: str) -> LLMClient | None:
        try:
            return import_string(path).from_env()
        except Exception:
            logger.warning("could not construct LLM client %s", path, exc_info=True)
            return None

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
