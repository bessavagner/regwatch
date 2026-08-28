import logging
from matching.models import Match
from enrichment.llm import LLMClient
from watches.grouping import term_texts

logger = logging.getLogger(__name__)


def enrich_match(match: Match, client: LLMClient) -> None:
    terms = term_texts(match.watch.groups)
    try:
        result = client.summarize(match.act.raw_text, terms)
    except Exception:
        logger.exception("enrichment failed for match %s", match.pk)
        return
    match.ai_summary = result.summary
    match.category = result.category
    match.confidence = result.confidence
    match.names_party = result.names_party
    match.has_amount = result.has_amount
    match.has_deadline = result.has_deadline
    match.signal_score = result.signal_score
    match.save(update_fields=[
        "ai_summary", "category", "confidence",
        "names_party", "has_amount", "has_deadline", "signal_score",
    ])
