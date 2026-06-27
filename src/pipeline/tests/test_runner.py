import pytest
from accounts.models import Workspace
from watches.models import Client, Watch
from digests.email import FakeEmailSender
from digests.models import Digest
from enrichment.llm import Summary, FakeLLMClient
from pipeline.runner import run_pipeline
from pipeline.tests.fixtures.sample_edition import sample_edition, DATE
from matching.models import Match


@pytest.fixture
def firm(db):
    ws = Workspace.objects.create(name="Acme Law")
    client = Client.objects.create(workspace=ws, name="Beta Corp", email="beta@example.test")
    Watch.objects.create(client=client, terms=["beta corp"])
    return client


@pytest.mark.django_db
def test_pipeline_produces_enriched_digest(firm):
    llm = FakeLLMClient(Summary("Licença concedida à Beta Corp.", "grant", 0.95))
    sender = FakeEmailSender()
    digests = run_pipeline([sample_edition()], llm, sender)

    assert len(digests) == 1
    assert Match.objects.count() == 1            # only the relevant act matched
    match = Match.objects.get()
    assert match.ai_summary == "Licença concedida à Beta Corp."
    assert match.category == "grant"
    assert "Licença concedida à Beta Corp." in digests[0].body
    assert len(sender.sent) == 1


@pytest.mark.django_db
def test_pipeline_is_idempotent(firm):
    llm = FakeLLMClient(Summary("ok", "grant", 0.9))
    run_pipeline([sample_edition()], llm, FakeEmailSender())
    run_pipeline([sample_edition()], llm, FakeEmailSender())
    assert Match.objects.count() == 1
    assert Digest.objects.filter(date=DATE).count() == 1


@pytest.mark.django_db
def test_run_pipeline_respects_max_enrich(firm):
    # sample_edition has one matching act ("beta corp"); cap of 0 enriches nothing.
    run_pipeline([sample_edition()], FakeLLMClient(Summary("x", "grant", 0.9)),
                 FakeEmailSender(), max_enrich=0)
    assert Match.objects.count() == 1
    assert Match.objects.get().ai_summary is None     # capped out -> never enriched
