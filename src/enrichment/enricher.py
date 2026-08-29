import logging
from matching.models import Match
from enrichment.llm import LLMClient
from watches.grouping import term_texts

logger = logging.getLogger(__name__)


def enrich_match(match: Match, client: LLMClient) -> None:
    # The terms that actually fired, when we know them. Every match created
    # before v0.20.0 carries an empty list -- those acts are past the text
    # retention window and cannot be re-evaluated, so they fall back to the
    # whole watch, which is what they were enriched with in the first place.
    terms = match.matched_terms or term_texts(match.watch.groups)
    try:
        result = client.summarize(match.act.raw_text, terms)
    except Exception:
        logger.exception("enrichment failed for match %s", match.pk)
        return
    match.ai_summary = result.summary
    match.category = result.category
    match.names_party = result.names_party
    match.has_amount = result.has_amount
    match.has_deadline = result.has_deadline
    match.signal_score = result.signal_score
    match.save(update_fields=[
        "ai_summary", "category",
        "names_party", "has_amount", "has_deadline", "signal_score",
    ])
