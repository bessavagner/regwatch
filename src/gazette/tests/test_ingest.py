import datetime
import pytest
from django.contrib.postgres.search import SearchQuery
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


@pytest.mark.django_db
def test_ingest_populates_the_portuguese_vector():
    edition = ingest_edition(RawEdition(
        date=datetime.date(2026, 6, 26), section="1",
        source_url="https://example.test/s1",
        items=(RawItem("a1", "Aviso", "Org", "extrato de contratos firmados", "#a1"),),
    ))
    act = Act.objects.get(edition=edition, identifier="a1")
    assert act.search_vector_pt is not None
    # 'contratos' must be reachable by the singular, which simple config cannot do.
    assert Act.objects.filter(
        pk=act.pk, search_vector_pt=SearchQuery("contrato", config="portuguese", search_type="phrase")
    ).exists()
