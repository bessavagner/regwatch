import datetime
import logging
from dataclasses import dataclass, field

from gazette.inlabs import fetch_editions
from gazette.ingest import ingest_edition
from gazette.models import Edition
from matching.matcher import match_edition
from enrichment.enricher import enrich_match
from enrichment.llm import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class BackfillResult:
    editions: int = 0
    acts: int = 0
    matches: int = 0
    enriched: int = 0
    skipped_dates: list[str] = field(default_factory=list)


def backfill_watch(
    date_from: datetime.date,
    date_to: datetime.date,
    llm: LLMClient,
    *,
    max_enrich: int | None = None,
) -> BackfillResult:
    result = BackfillResult()
    enriched = 0
    date = date_from
    while date <= date_to:
        editions = list(Edition.objects.filter(date=date))
        if not editions:
            try:
                raw_editions = fetch_editions(date)
            except Exception:
                logger.exception("backfill: fetch failed for %s — skipping", date)
                result.skipped_dates.append(date.isoformat())
                date += datetime.timedelta(days=1)
                continue
            if not raw_editions:
                result.skipped_dates.append(date.isoformat())
                date += datetime.timedelta(days=1)
                continue
            editions = [ingest_edition(raw) for raw in raw_editions]

        for edition in editions:
            result.editions += 1
            result.acts += edition.acts.count()
            for match in match_edition(edition):
                result.matches += 1
                if max_enrich is not None and enriched >= max_enrich:
                    continue
                enrich_match(match, llm)
                enriched += 1
                result.enriched += 1

        date += datetime.timedelta(days=1)

    return result
