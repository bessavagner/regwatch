import datetime
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import Workspace
from gazette.contracts import RawEdition, RawItem
from matching.models import Match
from watches.models import Client, Watch

DATE = datetime.date(2026, 6, 26)


@pytest.fixture
def firm(db):
    ws = Workspace.objects.create(name="BF")
    client = Client.objects.create(workspace=ws, name="Cactarus", email="c@example.test")
    Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "convênio", "kind": "concept"}]}])
    Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "jamais", "kind": "entity"}]}])
    return client


def _fake_fetch(monkeypatch, *, calls=None):
    def fetch(date):
        if calls is not None:
            calls.append(date)
        return [RawEdition(
            date=date, section="DO1", source_url=f"https://x.test/{date}",
            items=(RawItem("a1", "Portaria 1", "Org",
                           "Convênio firmado com o município.", "#a1"),),
        )]
    monkeypatch.setattr("pipeline.backfill.fetch_editions", fetch)


def _call(*args):
    out = StringIO()
    call_command("backfill_watches", *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_it_does_nothing_without_apply(firm, monkeypatch):
    calls = []
    _fake_fetch(monkeypatch, calls=calls)
    out = _call("--client", str(firm.pk), "--date-from", "2026-06-26", "--date-to", "2026-06-26")
    assert calls == []
    assert Match.objects.count() == 0
    assert "dry run" in out


@pytest.mark.django_db
def test_the_default_matches_without_calling_the_provider(firm, monkeypatch):
    # A coverage backtest asks "would this watch have fired", which needs no
    # summary. max_enrich=0 keeps it free, so a range can be re-run while terms
    # are being tuned.
    # No provider client is even constructed, so this passes with no API key
    # in the environment -- which is the point: the backtest must be runnable
    # without credentials and without spend.
    _fake_fetch(monkeypatch)
    _call("--client", str(firm.pk), "--date-from", "2026-06-26", "--date-to", "2026-06-26",
          "--apply")
    assert Match.objects.count() == 1


@pytest.mark.django_db
def test_it_reports_a_per_watch_breakdown(firm, monkeypatch):
    # The point of the command: which watch fired, not just how many matched.
    _fake_fetch(monkeypatch)
    out = _call("--client", str(firm.pk), "--date-from", "2026-06-26",
                "--date-to", "2026-06-26", "--apply")
    hit, missed = firm.watches.order_by("pk")
    assert f"watch {hit.pk}" in out
    assert f"watch {missed.pk}" in out
    # the silent one has to be visible as a zero, or a watch that matches
    # nothing looks the same as a watch that was never evaluated
    assert "0" in out


@pytest.mark.django_db
def test_an_unknown_client_is_an_error(firm):
    with pytest.raises(CommandError, match="no client"):
        _call("--client", "99999", "--date-from", "2026-06-26", "--date-to", "2026-06-26",
              "--apply")


@pytest.mark.django_db
def test_a_reversed_date_range_is_an_error(firm):
    with pytest.raises(CommandError, match="date-from"):
        _call("--client", str(firm.pk), "--date-from", "2026-06-27",
              "--date-to", "2026-06-26", "--apply")
