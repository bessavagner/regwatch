import datetime
import pytest
from gazette.contracts import RawEdition, RawItem
from gazette.models import Edition, Act
from gazette.ingest import ingest_edition


def _raw():
    return RawEdition(
        date=datetime.date(2026, 6, 26),
        section="1",
        source_url="https://example.test/dou/2026-06-26/s1",
        items=(
            RawItem("act-1", "Portaria Nº 12", "Ministério X",
                    "Concessão de licença à empresa Beta Corp.", "#act-1"),
        ),
    )


@pytest.mark.django_db
def test_ingest_creates_edition_and_acts():
    edition = ingest_edition(_raw())
    assert Edition.objects.count() == 1
    assert Act.objects.count() == 1
    act = Act.objects.get()
    assert act.edition == edition
    assert "beta corp" in act.search_text


@pytest.mark.django_db
def test_ingest_is_idempotent():
    ingest_edition(_raw())
    ingest_edition(_raw())
    assert Edition.objects.count() == 1
    assert Act.objects.count() == 1
