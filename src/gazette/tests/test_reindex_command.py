import datetime
import pytest
from django.core.management import call_command
from django.contrib.postgres.search import SearchQuery
from django.utils import timezone
from gazette.models import Act, Edition


@pytest.mark.django_db
def test_reindex_populates_rows_with_a_null_vector():
    edition = Edition.objects.create(
        date=datetime.date(2026, 6, 26), section="1", source_url="https://e.test/s1")
    act = Act.objects.create(
        edition=edition, identifier="a1", title="Aviso", agency="Org",
        raw_text="extrato de contratos firmados", search_text="extrato de contratos firmados",
        source_anchor="#a1")
    Act.objects.filter(pk=act.pk).update(search_vector_pt=None)

    call_command("reindex_search", "--batch-size", "1")

    assert Act.objects.filter(
        pk=act.pk,
        search_vector_pt=SearchQuery("contrato", config="portuguese", search_type="phrase"),
    ).exists()


@pytest.mark.django_db
def test_reindex_rebuilds_search_text_with_the_agency():
    edition = Edition.objects.create(
        date=datetime.date(2026, 6, 26), section="1", source_url="https://e.test/s1")
    act = Act.objects.create(
        edition=edition, identifier="a1", title="Portaria Nº 3",
        agency="Prefeituras/Estado do Ceará",
        raw_text="Dispensa de licitação.",
        # The pre-D8 shape: title + raw_text only.
        search_text="portaria no 3 dispensa de licitacao.",
        source_anchor="#a1")

    call_command("reindex_search", "--all", "--batch-size", "1")

    act.refresh_from_db()
    assert "estado do ceara" in act.search_text
    assert Act.objects.filter(
        pk=act.pk,
        search_vector_pt=SearchQuery("ceará", config="portuguese", search_type="phrase"),
    ).exists()


@pytest.mark.django_db
def test_reindex_leaves_pruned_acts_pruned():
    # prune_act_text empties raw_text/search_text and nulls the vector to hand
    # ~100 MB back to Postgres. Rebuilding those rows from the surviving title
    # and agency would re-inflate the GIN indexes the prune exists to shrink,
    # and would resurrect a searchable body for an act whose text we no longer
    # have. --all must not touch them.
    edition = Edition.objects.create(
        date=datetime.date(2026, 6, 1), section="1", source_url="https://e.test/s1",
        text_pruned_at=timezone.now())
    act = Act.objects.create(
        edition=edition, identifier="pruned", title="Portaria Nº 9",
        agency="Ministério X", raw_text="", search_text="", source_anchor="#p")

    call_command("reindex_search", "--all", "--batch-size", "1")

    act.refresh_from_db()
    assert act.search_text == ""
    assert act.search_vector_pt is None
