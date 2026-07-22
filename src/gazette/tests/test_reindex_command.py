import datetime
import pytest
from django.core.management import call_command
from django.contrib.postgres.search import SearchQuery
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
