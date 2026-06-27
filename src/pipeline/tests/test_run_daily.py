import datetime
import pytest
from django.core.management import call_command

from accounts.models import Workspace
from watches.models import Client, Watch
from enrichment.llm import Summary, FakeLLMClient
from digests.email import FakeEmailSender
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
    Watch.objects.create(client=c, terms=["beta corp"])
    return c


@pytest.mark.django_db
def test_run_daily_runs_pipeline_and_writes_runlog(firm, monkeypatch):
    sender = FakeEmailSender()
    monkeypatch.setattr("pipeline.management.commands.run_daily.fetch_editions",
                        lambda date: [_edition()])
    monkeypatch.setattr("pipeline.management.commands.run_daily.get_llm_client",
                        lambda: FakeLLMClient(Summary("ok", "grant", 0.9)))
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
