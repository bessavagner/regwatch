import logging
from matching.models import Match
from enrichment.llm import LLMClient

logger = logging.getLogger(__name__)


def enrich_match(match: Match, client: LLMClient) -> None:
    terms = list(match.watch.terms)
    try:
        result = client.summarize(match.act.raw_text, terms)
    except Exception:
        logger.exception("enrichment failed for match %s", match.pk)
        return
    match.ai_summary = result.summary
    match.category = result.category
    match.confidence = result.confidence
    match.save(update_fields=["ai_summary", "category", "confidence"])
