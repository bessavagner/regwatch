import datetime
import unicodedata
import pytest
from django.contrib.postgres.search import SearchQuery
from gazette.contracts import RawEdition, RawItem
from gazette.models import Edition, Act
from gazette.ingest import ingest_edition, ingest_edition_result
from gazette.normalize import normalize_pt


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


@pytest.mark.django_db
def test_ingest_matches_nfd_decomposed_raw_text_against_an_nfc_query():
    # 'licitações' with the cedilla+tilde built as combining characters
    # (NFD), the way some upstream gazette sources actually deliver text.
    nfd_word = unicodedata.normalize("NFD", "licitações")
    assert nfd_word != "licitações"  # sanity: this really is decomposed

    edition = ingest_edition(RawEdition(
        date=datetime.date(2026, 6, 26), section="1",
        source_url="https://example.test/s1",
        items=(RawItem("a1", "Aviso", "Org", f"extrato de {nfd_word} abertas", "#a1"),),
    ))
    act = Act.objects.get(edition=edition, identifier="a1")

    # The matcher builds its query the same way for a concept term.
    query = SearchQuery(normalize_pt("licitação"), config="portuguese", search_type="phrase")
    assert Act.objects.filter(pk=act.pk, search_vector_pt=query).exists()


@pytest.mark.django_db
def test_act_no_longer_has_the_simple_vector():
    assert not hasattr(Act(), "search_vector")


def _raw_two():
    return RawEdition(
        date=datetime.date(2026, 6, 26),
        section="1",
        source_url="https://example.test/dou/2026-06-26/s1",
        items=(
            RawItem("act-1", "Portaria Nº 12", "Ministério X", "Texto um.", "#act-1"),
            RawItem("act-2", "Portaria Nº 13", "Ministério Y", "Texto dois.", "#act-2"),
        ),
    )


def _xmin(act_pk):
    """The row version. Postgres bumps it on every UPDATE, even a no-op one."""
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute("SELECT xmin FROM gazette_act WHERE id = %s", [act_pk])
        return cur.fetchone()[0]


@pytest.mark.django_db
def test_ingest_reports_how_many_acts_it_wrote():
    result = ingest_edition_result(_raw_two())
    assert result.acts_written == 2
    assert result.edition.acts.count() == 2


@pytest.mark.django_db
def test_reingesting_identical_content_writes_nothing():
    """The 13:00 safety-net run re-parses a day the 08:05 run already stored.

    It used to push all ~3,500 rows through update_or_create plus a blanket
    search_vector rebuild, twice over, producing ~7,000 dead row-versions a day
    and the index bloat that made VACUUM FULL worth 100+ MB on 2026-08-20.
    """
    ingest_edition_result(_raw_two())
    before = {a.pk: _xmin(a.pk) for a in Act.objects.all()}

    result = ingest_edition_result(_raw_two())

    assert result.acts_written == 0
    assert {a.pk: _xmin(a.pk) for a in Act.objects.all()} == before, (
        "unchanged acts must not be rewritten"
    )


@pytest.mark.django_db
def test_reingesting_writes_only_the_acts_that_actually_changed():
    ingest_edition_result(_raw_two())
    untouched = Act.objects.get(identifier="act-1")
    untouched_xmin = _xmin(untouched.pk)

    amended = RawEdition(
        date=datetime.date(2026, 6, 26), section="1",
        source_url="https://example.test/dou/2026-06-26/s1",
        items=(
            RawItem("act-1", "Portaria Nº 12", "Ministério X", "Texto um.", "#act-1"),
            RawItem("act-2", "Portaria Nº 13", "Ministério Y", "Texto dois, retificado.", "#act-2"),
        ),
    )
    result = ingest_edition_result(amended)

    assert result.acts_written == 1
    assert _xmin(untouched.pk) == untouched_xmin
    assert "retificado" in Act.objects.get(identifier="act-2").search_text


@pytest.mark.django_db
def test_an_act_added_by_a_later_run_is_written_and_indexed():
    ingest_edition_result(_raw())

    grown = RawEdition(
        date=datetime.date(2026, 6, 26), section="1",
        source_url="https://example.test/dou/2026-06-26/s1",
        items=(
            RawItem("act-1", "Portaria Nº 12", "Ministério X",
                    "Concessão de licença à empresa Beta Corp.", "#act-1"),
            RawItem("act-9", "Aviso", "Org", "extrato de contratos firmados", "#act-9"),
        ),
    )
    result = ingest_edition_result(grown)

    assert result.acts_written == 1
    late = Act.objects.get(identifier="act-9")
    assert Act.objects.filter(
        pk=late.pk,
        search_vector_pt=SearchQuery("contrato", config="portuguese", search_type="phrase"),
    ).exists(), "a late-arriving act must still get its Portuguese vector"


@pytest.mark.django_db
def test_a_changed_act_gets_its_vector_rebuilt():
    ingest_edition_result(_raw())
    amended = RawEdition(
        date=datetime.date(2026, 6, 26), section="1",
        source_url="https://example.test/dou/2026-06-26/s1",
        items=(RawItem("act-1", "Portaria Nº 12", "Ministério X",
                       "extrato de contratos firmados", "#act-1"),),
    )
    ingest_edition_result(amended)

    act = Act.objects.get(identifier="act-1")
    assert Act.objects.filter(
        pk=act.pk,
        search_vector_pt=SearchQuery("contrato", config="portuguese", search_type="phrase"),
    ).exists()
    assert not Act.objects.filter(
        pk=act.pk,
        search_vector_pt=SearchQuery("licença", config="portuguese", search_type="phrase"),
    ).exists(), "the stale vector must not survive the rewrite"


@pytest.mark.django_db
def test_ingest_edition_still_returns_the_edition():
    """~20 call sites unpack a bare Edition; the counted variant is additive."""
    edition = ingest_edition(_raw())
    assert isinstance(edition, Edition)


@pytest.mark.django_db
def test_ingest_puts_the_agency_into_search_text():
    # 'Hidrolândia' exists in both Ceará and Goiás; the publishing body is the
    # only field that separates them, so it has to be searchable.
    edition = ingest_edition(RawEdition(
        date=datetime.date(2026, 6, 26), section="1",
        source_url="https://example.test/s1",
        items=(RawItem("a1", "Portaria Nº 3",
                       "Prefeituras/Estado do Ceará/Prefeitura Municipal de Hidrolândia",
                       "Dispensa de licitação.", "#a1"),),
    ))
    act = Act.objects.get(edition=edition, identifier="a1")
    assert "estado do ceara" in act.search_text
    assert "dispensa de licitacao" in act.search_text


@pytest.mark.django_db
def test_ingest_puts_the_agency_into_the_portuguese_vector():
    edition = ingest_edition(RawEdition(
        date=datetime.date(2026, 6, 26), section="1",
        source_url="https://example.test/s1",
        items=(RawItem("a1", "Portaria Nº 3", "Ministério da Educação",
                       "Texto sem o nome do órgão.", "#a1"),),
    ))
    act = Act.objects.get(edition=edition, identifier="a1")
    assert Act.objects.filter(
        pk=act.pk,
        search_vector_pt=SearchQuery("educação", config="portuguese", search_type="phrase"),
    ).exists()
