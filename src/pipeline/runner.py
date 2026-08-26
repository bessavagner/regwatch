import datetime
from dataclasses import dataclass, field

from django.conf import settings

from gazette.contracts import RawEdition
from gazette.ingest import ingest_edition_result
from matching.matcher import match_edition
from enrichment.enricher import enrich_match
from enrichment.llm import LLMClient
from digests.email import EmailSender
from digests.notifier import build_and_send_digests, retry_unsent_digests


@dataclass
class RunResult:
    """What one run did, as opposed to what exists for the date afterwards."""

    ingested_acts: int = 0
    created_matches: int = 0
    created_enriched: int = 0
    digests: list = field(default_factory=list)


def run_pipeline(
    raw_editions: list[RawEdition],
    llm: LLMClient,
    sender: EmailSender,
    *,
    max_enrich: int | None = None,
    today: datetime.date | None = None,
) -> RunResult:
    result = RunResult()
    dates = set()
    enriched = 0
    for raw in raw_editions:
        # acts_written, not len(raw.items): a re-run over a day already stored
        # parses the same acts but writes none, and the counter must say so.
        ingested = ingest_edition_result(raw)
        result.ingested_acts += ingested.acts_written
        edition = ingested.edition
        dates.add(edition.date)
        # match_edition returns only the matches it created, so a re-run over a
        # day already processed correctly reports zero created and zero
        # enriched rather than repeating the first run's numbers.
        for match in match_edition(edition):
            result.created_matches += 1
            if max_enrich is not None and enriched >= max_enrich:
                continue
            enrich_match(match, llm)
            enriched += 1
    result.created_enriched = enriched

    digests = []
    for date in sorted(dates):
        digests.extend(build_and_send_digests(date, sender))

    # Drain anything an earlier run failed to deliver. Runs after this run's own
    # digests so a fresh outage is recorded before older ones are re-attempted.
    anchor = today or max(dates, default=None)
    if anchor is not None:
        window = datetime.timedelta(days=settings.REGWATCH_DIGEST_RETRY_DAYS)
        retry_unsent_digests(anchor - window, anchor, sender)

    result.digests = digests
    return result
