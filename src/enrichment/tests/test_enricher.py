import datetime
import pytest
from accounts.models import Workspace
from watches.models import Client, Watch
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from gazette.models import Act, Edition
from matching.matcher import match_edition
from matching.models import Match
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
    fake = FakeLLMClient(Summary("Licença concedida.", "grant"))
    enrich_match(a_match, fake)
    a_match.refresh_from_db()
    assert a_match.ai_summary == "Licença concedida."
    assert a_match.category == "grant"


@pytest.mark.django_db
def test_enrich_swallows_llm_failure(a_match):
    enrich_match(a_match, RaisingLLMClient())
    a_match.refresh_from_db()
    assert a_match.ai_summary is None
    assert a_match.category == ""


class _RecordingLLM:
    def __init__(self):
        self.seen_terms = None

    def summarize(self, text, terms):
        self.seen_terms = terms
        return Summary(summary="s", category="c")


@pytest.mark.django_db
def test_enricher_passes_only_the_terms_that_fired():
    ws = Workspace.objects.create(name="EnrWS")
    client = Client.objects.create(workspace=ws, name="Enr")
    watch = Watch.objects.create(client=client, groups=[
        {"terms": [{"text": "sebrae", "kind": "entity"}]},
        {"terms": [{"text": "contrato", "kind": "concept"}]},
    ])
    edition = Edition.objects.create(
        date=datetime.date(2026, 6, 26), section="1", source_url="https://e.test/s1")
    act = Act.objects.create(
        edition=edition, identifier="a1", title="t", agency="g",
        raw_text="corpo", search_text="corpo", source_anchor="#a1")
    match = Match.objects.create(
        watch=watch, act=act, rank=0.0, snippet="corpo", matched_terms=["contrato"])

    llm = _RecordingLLM()
    enrich_match(match, llm)
    assert llm.seen_terms == ["contrato"]


@pytest.mark.django_db
def test_enricher_falls_back_to_the_whole_watch_for_pre_v0_20_matches():
    # Every match created before v0.20.0 carries an empty matched_terms and the
    # terms are unrecoverable -- acts past the 7-day text window have no body to
    # re-evaluate. Those still get the full watch, which is what they got before.
    ws = Workspace.objects.create(name="OldWS")
    client = Client.objects.create(workspace=ws, name="Old")
    watch = Watch.objects.create(client=client, groups=[
        {"terms": [{"text": "sebrae", "kind": "entity"}]},
        {"terms": [{"text": "contrato", "kind": "concept"}]},
    ])
    edition = Edition.objects.create(
        date=datetime.date(2026, 6, 26), section="1", source_url="https://o.test/s1")
    act = Act.objects.create(
        edition=edition, identifier="o1", title="t", agency="g",
        raw_text="corpo", search_text="corpo", source_anchor="#o1")
    match = Match.objects.create(
        watch=watch, act=act, rank=0.0, snippet="corpo", matched_terms=[])

    llm = _RecordingLLM()
    enrich_match(match, llm)
    assert llm.seen_terms == ["sebrae", "contrato"]


@pytest.mark.django_db
def test_enrich_stores_the_signals_and_their_score(a_match):
    fake = FakeLLMClient(Summary(
        "Contrato de R$ 1.000,00 com a Beta Corp até 30/09.", "tender",
        names_party=True, has_amount=True, has_deadline=False,
    ))
    enrich_match(a_match, fake)
    a_match.refresh_from_db()
    assert a_match.names_party is True
    assert a_match.has_amount is True
    assert a_match.has_deadline is False
    assert a_match.signal_score == 2


@pytest.mark.django_db
def test_a_failed_enrichment_leaves_the_score_at_zero(a_match):
    enrich_match(a_match, RaisingLLMClient())
    a_match.refresh_from_db()
    assert a_match.signal_score == 0
