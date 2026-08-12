import datetime

from django.conf import settings

from gazette.contracts import RawEdition
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from enrichment.enricher import enrich_match
from enrichment.llm import LLMClient
from digests.email import EmailSender
from digests.notifier import build_and_send_digests, retry_unsent_digests


def run_pipeline(
    raw_editions: list[RawEdition],
    llm: LLMClient,
    sender: EmailSender,
    *,
    max_enrich: int | None = None,
    today: datetime.date | None = None,
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

    # Drain anything an earlier run failed to deliver. Runs after this run's own
    # digests so a fresh outage is recorded before older ones are re-attempted.
    anchor = today or max(dates, default=None)
    if anchor is not None:
        window = datetime.timedelta(days=settings.REGWATCH_DIGEST_RETRY_DAYS)
        retry_unsent_digests(anchor - window, anchor, sender)

    return digests
