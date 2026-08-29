import datetime
import pytest
from django.core.management import call_command

from accounts.models import Workspace
from watches.models import Client, Watch
from enrichment.llm import Summary, FakeLLMClient
from digests.email import FakeEmailSender
from digests.email import RaisingEmailSender
from digests.models import Digest
from gazette.contracts import RawEdition, RawItem
from pipeline.models import RunLog

DATE = datetime.date(2026, 6, 26)


def _edition():
    return RawEdition(
        date=DATE, section="DO1", source_url="https://x/DO1",
        items=(RawItem("a1", "Portaria 1", "Min X", "Licença à BETA CORP.", "#a1"),),
    )


@pytest.fixture
def firm(db):
    ws = Workspace.objects.create(name="Acme")
    c = Client.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    Watch.objects.create(client=c, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}])
    return c


@pytest.mark.django_db
def test_run_daily_runs_pipeline_and_writes_runlog(firm, monkeypatch):
    sender = FakeEmailSender()
    monkeypatch.setattr("pipeline.management.commands.run_daily.fetch_editions",
                        lambda date: [_edition()])
    monkeypatch.setattr("pipeline.management.commands.run_daily.get_llm_client",
                        lambda: FakeLLMClient(Summary("ok", "grant")))
    monkeypatch.setattr("pipeline.management.commands.run_daily.get_email_sender",
                        lambda: sender)

    call_command("run_daily", date="2026-06-26")

    assert len(sender.sent) == 1
    log = RunLog.objects.get(date=DATE)
    assert log.status == "success"
    assert log.editions == 1 and log.acts == 1 and log.matches == 1
    assert log.enriched == 1 and log.digests == 1
    assert log.finished_at is not None


@pytest.mark.django_db
def test_run_daily_records_failure_and_reraises(monkeypatch):
    def boom(date):
        raise RuntimeError("inlabs down")
    monkeypatch.setattr("pipeline.management.commands.run_daily.fetch_editions", boom)

    with pytest.raises(RuntimeError):
        call_command("run_daily", date="2026-06-26")
    log = RunLog.objects.get(date=DATE)
    assert log.status == "failed"
    assert "inlabs down" in log.errors
    assert log.finished_at is not None


@pytest.fixture
def client_with_unsent_digest(db):
    ws = Workspace.objects.create(name="Acme")
    c = Client.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    Digest.objects.create(client=c, date=DATE, body="body", sent=False)
    return c


def _no_editions(monkeypatch, sender):
    """Run the command with nothing to scrape and a sender we control.

    run_daily resolves the LLM client and the email sender through
    pipeline.adapters, which read REGWATCH_* settings and go to the real
    providers; both seams have to be stubbed or the command raises before it
    ever computes a status.
    """
    monkeypatch.setattr(
        "pipeline.management.commands.run_daily.fetch_editions", lambda d: []
    )
    monkeypatch.setattr(
        "pipeline.management.commands.run_daily.get_llm_client",
        lambda: FakeLLMClient(Summary("ok", "grant")),
    )
    monkeypatch.setattr(
        "pipeline.management.commands.run_daily.get_email_sender", lambda: sender
    )


@pytest.mark.django_db
def test_run_is_partial_when_a_digest_was_not_delivered(
    client_with_unsent_digest, monkeypatch
):
    # The sender still refuses, so the backlog sweep cannot rescue the digest —
    # which is exactly the 2026-08-05..11 outage the status has to stop hiding.
    _no_editions(monkeypatch, RaisingEmailSender("535 BadCredentials"))
    call_command("run_daily", "--date", DATE.isoformat())

    log = RunLog.objects.get(date=DATE, trigger="scheduled")
    assert log.digests_sent == 0
    assert log.digests == 1
    assert log.status == "partial"
    assert "digest" in log.errors.lower()


@pytest.mark.django_db
def test_run_is_success_when_everything_was_delivered(
    client_with_unsent_digest, monkeypatch
):
    Digest.objects.update(sent=True)
    _no_editions(monkeypatch, FakeEmailSender())
    call_command("run_daily", "--date", DATE.isoformat())

    log = RunLog.objects.get(date=DATE, trigger="scheduled")
    assert log.status == "success"
    assert log.digests_sent == 1


@pytest.mark.django_db
def test_runlog_separates_this_run_from_the_date_total(firm, monkeypatch):
    """The midday re-run must not re-report the morning's work as its own.

    The date-scoped totals deliberately still show the day's true state — the
    heartbeat reads only the latest run of a date and would otherwise mask a
    morning partial behind a quiet midday run that created nothing.
    """
    monkeypatch.setattr(
        "pipeline.management.commands.run_daily.fetch_editions",
        lambda date: [_edition()],
    )
    llm = FakeLLMClient(Summary("ok", "grant"))
    monkeypatch.setattr("pipeline.management.commands.run_daily.get_llm_client", lambda: llm)
    monkeypatch.setattr(
        "pipeline.management.commands.run_daily.get_email_sender", lambda: FakeEmailSender()
    )

    call_command("run_daily", "--date", DATE.isoformat())
    call_command("run_daily", "--date", DATE.isoformat())

    morning, midday = RunLog.objects.filter(date=DATE).order_by("started_at")

    assert (morning.ingested_acts, morning.created_matches, morning.created_enriched) == (1, 1, 1)
    # All three zero: the midday run re-parsed the edition but the content was
    # unchanged, so it wrote no act rows either.
    assert (midday.ingested_acts, midday.created_matches, midday.created_enriched) == (0, 0, 0)

    # The day still holds exactly one match, and both rows report that.
    assert morning.matches == midday.matches == 1
    assert midday.status == "success"
