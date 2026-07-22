from django.contrib.postgres.search import SearchVector
from gazette.contracts import RawEdition
from gazette.models import Edition, Act
from gazette.normalize import normalize_text


def ingest_edition(raw: RawEdition) -> Edition:
    edition, _ = Edition.objects.update_or_create(
        date=raw.date, section=raw.section,
        defaults={"source_url": raw.source_url},
    )
    for item in raw.items:
        Act.objects.update_or_create(
            edition=edition, identifier=item.identifier,
            defaults={
                "title": item.title,
                "agency": item.agency,
                "raw_text": item.raw_text,
                "search_text": normalize_text(f"{item.title} {item.raw_text}"),
                "source_anchor": item.source_anchor,
            },
        )
    Act.objects.filter(edition=edition).update(
        search_vector=SearchVector("search_text", config="simple"),
        # Built from the raw fields, not from search_text: to_tsvector case-folds
        # on its own, and search_text has already had its accents stripped, which
        # would defeat the stemmer.
        search_vector_pt=SearchVector("title", "raw_text", config="portuguese"),
    )
    return edition
