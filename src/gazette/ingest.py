from dataclasses import dataclass

from django.contrib.postgres.search import SearchVector
from django.db.models import F
from gazette.contracts import RawEdition
from gazette.models import Edition, Act
from gazette.normalize import NormalizeNFC, normalize_text

# The act fields ingest owns. Everything else on Act (search_vector_pt) is
# derived below; anything not listed here is never touched by a re-ingest.
CONTENT_FIELDS = ("title", "agency", "raw_text", "search_text", "source_anchor")

BATCH = 1000


@dataclass(frozen=True)
class IngestResult:
    """What one ingest actually wrote, as opposed to what it was handed.

    `acts_written` counts rows created or changed — not `len(raw.items)`. The
    13:00 safety-net run re-parses a day the 08:05 run already stored, so the
    difference is the whole point: a re-run over unchanged content writes zero.
    """

    edition: Edition
    acts_written: int


def _content_of(item) -> dict:
    return {
        "title": item.title,
        "agency": item.agency,
        "raw_text": item.raw_text,
        "search_text": normalize_text(f"{item.title} {item.raw_text}"),
        "source_anchor": item.source_anchor,
    }


def ingest_edition_result(raw: RawEdition) -> IngestResult:
    edition, _ = Edition.objects.update_or_create(
        date=raw.date, section=raw.section,
        defaults={"source_url": raw.source_url, "text_pruned_at": None},
    )

    existing = {a.identifier: a for a in Act.objects.filter(edition=edition)}
    to_create, to_update = [], []
    for item in raw.items:
        content = _content_of(item)
        act = existing.get(item.identifier)
        if act is None:
            to_create.append(Act(edition=edition, identifier=item.identifier, **content))
        elif any(getattr(act, f) != content[f] for f in CONTENT_FIELDS):
            # Compared in Python rather than left to update_or_create, which
            # issues its UPDATE unconditionally: re-writing ~3,500 byte-identical
            # rows twice a day is what bloated the trigram and GIN indexes to
            # 107 MB by 2026-08-26 (docs/analysis/2026-08-26-production-re-evaluation.md).
            for field, value in content.items():
                setattr(act, field, value)
            to_update.append(act)

    Act.objects.bulk_create(to_create, batch_size=BATCH)
    Act.objects.bulk_update(to_update, CONTENT_FIELDS, batch_size=BATCH)

    written = [a.pk for a in to_create] + [a.pk for a in to_update]
    if written:
        # Scoped to the rows just written, not the whole edition: the vector is
        # a pure function of title+raw_text, so an untouched act's vector is
        # already correct and rebuilding it only churns the GIN index.
        Act.objects.filter(pk__in=written).update(
            # Built from the raw fields, not from search_text: to_tsvector case-folds
            # on its own, and search_text has already had its accents stripped, which
            # would defeat the stemmer. NFC-normalised so it agrees with the
            # NFC-normalised queries the matcher issues (gazette.normalize.normalize_pt);
            # some upstream text arrives NFD-decomposed, which would otherwise stem
            # differently and silently miss.
            search_vector_pt=SearchVector(
                NormalizeNFC(F("title")), NormalizeNFC(F("raw_text")), config="portuguese"
            ),
        )
    return IngestResult(edition, len(written))


def ingest_edition(raw: RawEdition) -> Edition:
    """Ingest and return just the Edition, for callers that don't count."""
    return ingest_edition_result(raw).edition
