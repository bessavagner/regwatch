import datetime

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Membership, Workspace
from watches.models import Client as WatchClient
from watches.models import Watch
from gazette.contracts import RawEdition, RawItem
from enrichment.llm import Summary, FakeLLMClient
from matching.models import Match
from pipeline.models import RunLog

User = get_user_model()


def _member(name, email):
    ws = Workspace.objects.create(name=name)
    user = User.objects.create_user(username=email, email=email, password="pw12345")
    Membership.objects.create(workspace=ws, user=user)
    return ws, user


@pytest.fixture
def firm_a(db):
    return _member("Firm A", "a@firm.com")


@pytest.fixture
def firm_b(db):
    return _member("Firm B", "b@firm.com")


def _raw_edition(date):
    return RawEdition(
        date=date, section="DO1", source_url=f"https://x.test/{date}",
        items=(RawItem("a1", "Portaria 1", "Org", "Licença à BETA CORP.", "#a1"),),
    )


@pytest.mark.django_db
def test_backfill_404s_for_a_watch_outside_the_callers_workspace(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    b_client = WatchClient.objects.create(workspace=ws_b, name="B-client")
    b_watch = Watch.objects.create(
        client=b_client, groups=[{"terms": [{"text": "x", "kind": "entity"}]}]
    )
    api = APIClient()
    api.force_authenticate(user=user_a)
    resp = api.post(
        f"/api/watches/{b_watch.id}/backfill",
        {"date_from": "2026-06-26", "date_to": "2026-06-26"},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_backfill_rejects_date_from_after_date_to(firm_a):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(
        f"/api/watches/{watch.id}/backfill",
        {"date_from": "2026-06-27", "date_to": "2026-06-26"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_backfill_rejects_a_span_over_seven_days(firm_a):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(
        f"/api/watches/{watch.id}/backfill",
        {"date_from": "2026-06-01", "date_to": "2026-06-08"},  # 8 calendar dates
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_backfill_rejects_a_future_date_to(firm_a):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(
        f"/api/watches/{watch.id}/backfill",
        {"date_from": "2099-01-01", "date_to": "2099-01-01"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_backfill_runs_and_writes_a_backfill_runlog(firm_a, monkeypatch):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    monkeypatch.setattr("pipeline.backfill.fetch_editions", lambda date: [_raw_edition(date)])
    monkeypatch.setattr("watches.api.get_llm_client", lambda: FakeLLMClient(Summary("ok", "grant", 0.9)))

    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(
        f"/api/watches/{watch.id}/backfill",
        {"date_from": "2026-06-26", "date_to": "2026-06-26"},
        format="json",
    )

    assert resp.status_code == 200
    assert resp.data == {"editions": 1, "acts": 1, "matches": 1, "enriched": 1, "skipped_dates": []}
    log = RunLog.objects.get(trigger="backfill")
    assert log.status == "success"
    assert log.editions == 1 and log.matches == 1
    assert log.finished_at is not None


@pytest.mark.django_db
def test_backfill_reports_skipped_dates_on_partial_failure(firm_a, monkeypatch):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )

    def fake_fetch(date):
        if date == datetime.date(2026, 6, 26):
            raise RuntimeError("inlabs down")
        return [_raw_edition(date)]
    monkeypatch.setattr("pipeline.backfill.fetch_editions", fake_fetch)
    monkeypatch.setattr("watches.api.get_llm_client", lambda: FakeLLMClient(Summary("ok", "grant", 0.9)))

    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(
        f"/api/watches/{watch.id}/backfill",
        {"date_from": "2026-06-26", "date_to": "2026-06-27"},
        format="json",
    )

    assert resp.status_code == 200
    assert resp.data["skipped_dates"] == ["2026-06-26"]
    assert resp.data["editions"] == 1


@pytest.mark.django_db
def test_backfill_respects_the_enrich_cap(firm_a, monkeypatch, settings):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    settings.REGWATCH_MAX_ENRICH_PER_BACKFILL = 0
    monkeypatch.setattr("pipeline.backfill.fetch_editions", lambda date: [_raw_edition(date)])
    monkeypatch.setattr("watches.api.get_llm_client", lambda: FakeLLMClient(Summary("ok", "grant", 0.9)))

    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(
        f"/api/watches/{watch.id}/backfill",
        {"date_from": "2026-06-26", "date_to": "2026-06-26"},
        format="json",
    )

    assert resp.data["matches"] == 1
    assert resp.data["enriched"] == 0


@pytest.mark.django_db
def test_backfill_uses_the_backfill_specific_enrich_cap_not_the_run_daily_one(firm_a, monkeypatch, settings):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    # run_daily's budget stays generous (no HTTP timeout pressure); the interactive
    # backfill endpoint must use its own, much smaller budget so a real request
    # can't run long enough to hit gunicorn's worker timeout.
    settings.REGWATCH_MAX_ENRICH_PER_RUN = 200
    settings.REGWATCH_MAX_ENRICH_PER_BACKFILL = 0
    monkeypatch.setattr("pipeline.backfill.fetch_editions", lambda date: [_raw_edition(date)])
    monkeypatch.setattr("watches.api.get_llm_client", lambda: FakeLLMClient(Summary("ok", "grant", 0.9)))

    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(
        f"/api/watches/{watch.id}/backfill",
        {"date_from": "2026-06-26", "date_to": "2026-06-26"},
        format="json",
    )

    assert resp.data["matches"] == 1
    assert resp.data["enriched"] == 0


@pytest.mark.django_db
def test_backfill_is_idempotent_across_requests(firm_a, monkeypatch):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    monkeypatch.setattr("pipeline.backfill.fetch_editions", lambda date: [_raw_edition(date)])
    monkeypatch.setattr("watches.api.get_llm_client", lambda: FakeLLMClient(Summary("ok", "grant", 0.9)))

    api = APIClient()
    api.force_authenticate(user=user)
    body = {"date_from": "2026-06-26", "date_to": "2026-06-26"}
    first = api.post(f"/api/watches/{watch.id}/backfill", body, format="json")
    second = api.post(f"/api/watches/{watch.id}/backfill", body, format="json")

    assert first.data["matches"] == 1
    assert second.data["matches"] == 0
    assert Match.objects.count() == 1


@pytest.mark.django_db
def test_backfill_response_does_not_reveal_other_workspaces_match_counts(firm_a, firm_b, monkeypatch):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    client_a = WatchClient.objects.create(workspace=ws_a, name="Beta")
    watch_a = Watch.objects.create(
        client=client_a, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    # A watch in a DIFFERENT workspace that also matches — match_edition() matches
    # every active watch system-wide, so this incidentally matches too. The response
    # must not reveal that to the calling user.
    client_b = WatchClient.objects.create(workspace=ws_b, name="Gamma")
    Watch.objects.create(
        client=client_b, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    monkeypatch.setattr("pipeline.backfill.fetch_editions", lambda date: [_raw_edition(date)])
    monkeypatch.setattr("watches.api.get_llm_client", lambda: FakeLLMClient(Summary("ok", "grant", 0.9)))

    api = APIClient()
    api.force_authenticate(user=user_a)
    resp = api.post(
        f"/api/watches/{watch_a.id}/backfill",
        {"date_from": "2026-06-26", "date_to": "2026-06-26"},
        format="json",
    )

    assert resp.status_code == 200
    assert resp.data["matches"] == 1     # only firm A's watch is counted, not firm B's
    assert resp.data["enriched"] == 1
    assert Match.objects.count() == 2    # firm B's watch still matched too, just not reported
