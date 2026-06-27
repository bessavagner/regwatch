from gazette.contracts import RawEdition
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from enrichment.enricher import enrich_match
from enrichment.llm import LLMClient
from digests.email import EmailSender
from digests.notifier import build_and_send_digests


def run_pipeline(
    raw_editions: list[RawEdition],
    llm: LLMClient,
    sender: EmailSender,
    *,
    max_enrich: int | None = None,
):
    dates = set()
    enriched = 0
    for raw in raw_editions:
        edition = ingest_edition(raw)
        dates.add(edition.date)
        for match in match_edition(edition):
            if max_enrich is not None and enriched >= max_enrich:
                continue
            enrich_match(match, llm)
            enriched += 1

    digests = []
    for date in sorted(dates):
        digests.extend(build_and_send_digests(date, sender))
    return digests
