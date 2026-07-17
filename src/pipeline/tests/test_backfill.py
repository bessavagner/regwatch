import datetime

import pytest

from accounts.models import Workspace
from watches.models import Client, Watch
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from gazette.models import Edition
from matching.models import Match
from digests.models import Digest
from enrichment.llm import Summary, FakeLLMClient
from pipeline.backfill import backfill_watch

DATE = datetime.date(2026, 6, 26)
DATE2 = datetime.date(2026, 6, 27)


def _raw_edition(date, identifier="a1", text="Licença à BETA CORP."):
    return RawEdition(
        date=date, section="DO1", source_url=f"https://x.test/{date}",
        items=(RawItem(identifier, "Portaria 1", "Org", text, "#a1"),),
    )


@pytest.fixture
def firm(db):
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    Watch.objects.create(client=client, terms=["beta corp"])
    return client


@pytest.mark.django_db
def test_backfill_fetches_and_matches_a_missing_date(firm, monkeypatch):
    monkeypatch.setattr("pipeline.backfill.fetch_editions", lambda date: [_raw_edition(date)])
    llm = FakeLLMClient(Summary("ok", "grant", 0.9))

    result = backfill_watch(DATE, DATE, llm, max_enrich=10)

    assert result.editions == 1
    assert result.acts == 1
    assert result.matches == 1
    assert result.enriched == 1
    assert result.skipped_dates == []
    assert Match.objects.count() == 1


@pytest.mark.django_db
def test_backfill_reuses_an_already_ingested_date_without_refetching(firm, monkeypatch):
    ingest_edition(_raw_edition(DATE))  # simulate the day already having been run
    # a NEW watch, created after that date was originally processed
    other_client = Client.objects.create(workspace=firm.workspace, name="Gamma")
    Watch.objects.create(client=other_client, terms=["beta corp"])

    def boom(date):
        raise AssertionError("fetch_editions must not be called for an already-ingested date")
    monkeypatch.setattr("pipeline.backfill.fetch_editions", boom)

    result = backfill_watch(DATE, DATE, FakeLLMClient(Summary("ok", "grant", 0.9)), max_enrich=10)

    assert result.editions == 1
    assert result.matches == 2   # both the original watch and the new one match
    assert Match.objects.filter(watch__client=other_client).count() == 1


@pytest.mark.django_db
def test_backfill_records_skipped_date_when_nothing_published(firm, monkeypatch):
    monkeypatch.setattr("pipeline.backfill.fetch_editions", lambda date: [])
    result = backfill_watch(DATE, DATE, FakeLLMClient(Summary("ok", "grant", 0.9)))
    assert result.skipped_dates == [DATE.isoformat()]
    assert result.editions == 0
    assert Edition.objects.count() == 0


@pytest.mark.django_db
def test_backfill_skips_a_failing_date_and_continues_the_range(firm, monkeypatch):
    def fake_fetch(date):
        if date == DATE:
            raise RuntimeError("inlabs down")
        return [_raw_edition(date)]
    monkeypatch.setattr("pipeline.backfill.fetch_editions", fake_fetch)

    result = backfill_watch(DATE, DATE2, FakeLLMClient(Summary("ok", "grant", 0.9)), max_enrich=10)

    assert result.skipped_dates == [DATE.isoformat()]
    assert result.editions == 1          # only DATE2 succeeded
    assert result.matches == 1


@pytest.mark.django_db
def test_backfill_respects_max_enrich_across_the_whole_range(firm, monkeypatch):
    monkeypatch.setattr(
        "pipeline.backfill.fetch_editions",
        lambda date: [_raw_edition(date, identifier=f"a-{date}")],
    )

    result = backfill_watch(DATE, DATE2, FakeLLMClient(Summary("ok", "grant", 0.9)), max_enrich=1)

    assert result.matches == 2      # one match per date
    assert result.enriched == 1     # capped
    assert Match.objects.exclude(ai_summary__isnull=True).count() == 1


@pytest.mark.django_db
def test_backfill_is_idempotent_on_rerun(firm, monkeypatch):
    calls = []

    def fake_fetch(date):
        calls.append(date)
        return [_raw_edition(date)]
    monkeypatch.setattr("pipeline.backfill.fetch_editions", fake_fetch)
    llm = FakeLLMClient(Summary("ok", "grant", 0.9))

    first = backfill_watch(DATE, DATE, llm, max_enrich=10)
    second = backfill_watch(DATE, DATE, llm, max_enrich=10)

    assert first.matches == 1
    assert second.matches == 0          # already matched — get_or_create found it
    assert Match.objects.count() == 1
    assert calls == [DATE]              # second run reused the already-ingested edition


@pytest.mark.django_db
def test_backfill_never_sends_a_digest(firm, monkeypatch):
    monkeypatch.setattr("pipeline.backfill.fetch_editions", lambda date: [_raw_edition(date)])
    backfill_watch(DATE, DATE, FakeLLMClient(Summary("ok", "grant", 0.9)), max_enrich=10)
    assert Digest.objects.count() == 0
