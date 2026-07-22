import datetime
import pytest
from accounts.models import Workspace
from watches.models import Client, Watch
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from enrichment.llm import Summary, FakeLLMClient, RaisingLLMClient
from enrichment.enricher import enrich_match


@pytest.fixture
def a_match(db):
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta")
    Watch.objects.create(client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}])
    edition = ingest_edition(RawEdition(
        date=datetime.date(2026, 6, 26), section="1", source_url="https://x.test/s1",
        items=(RawItem("a1", "Ato", "Org", "Licença à BETA CORP.", "#a1"),),
    ))
    return match_edition(edition)[0]


@pytest.mark.django_db
def test_enrich_sets_summary_and_category(a_match):
    fake = FakeLLMClient(Summary("Licença concedida.", "grant", 0.9))
    enrich_match(a_match, fake)
    a_match.refresh_from_db()
    assert a_match.ai_summary == "Licença concedida."
    assert a_match.category == "grant"
    assert a_match.confidence == 0.9


@pytest.mark.django_db
def test_enrich_swallows_llm_failure(a_match):
    enrich_match(a_match, RaisingLLMClient())
    a_match.refresh_from_db()
    assert a_match.ai_summary is None
    assert a_match.category == ""
