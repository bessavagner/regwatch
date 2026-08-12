import datetime

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from pipeline.models import RunLog

DATE = datetime.date(2026, 6, 26)


@pytest.mark.django_db
def test_heartbeat_ok_when_success_runlog_exists():
    RunLog.objects.create(date=DATE, status="success")
    call_command("check_heartbeat", date="2026-06-26")   # no raise == exit 0


@pytest.mark.django_db
def test_heartbeat_fails_when_no_runlog():
    with pytest.raises(CommandError):
        call_command("check_heartbeat", date="2026-06-26")


@pytest.mark.django_db
def test_heartbeat_fails_when_only_non_success_runlog():
    RunLog.objects.create(date=DATE, status="failed")
    with pytest.raises(CommandError):
        call_command("check_heartbeat", date="2026-06-26")


@pytest.mark.django_db
def test_heartbeat_fails_when_only_a_backfill_runlog_exists_for_the_date():
    RunLog.objects.create(date=DATE, status="success", trigger="backfill")
    with pytest.raises(CommandError):
        call_command("check_heartbeat", date="2026-06-26")


@pytest.mark.django_db
def test_heartbeat_passes_for_a_clean_run():
    RunLog.objects.create(date=DATE, status="success", trigger="scheduled",
                          matches=3, enriched=3, digests=1, digests_sent=1)
    call_command("check_heartbeat", "--date", DATE.isoformat())


@pytest.mark.django_db
def test_heartbeat_fails_when_the_run_only_partly_succeeded():
    RunLog.objects.create(date=DATE, status="partial", trigger="scheduled",
                          matches=3, enriched=3, digests=1, digests_sent=0,
                          errors="1 digests not sent")
    with pytest.raises(CommandError) as excinfo:
        call_command("check_heartbeat", "--date", DATE.isoformat())
    assert "1 digests not sent" in str(excinfo.value)


@pytest.mark.django_db
def test_heartbeat_fails_when_a_digest_for_the_date_is_still_unsent():
    # The run itself looked clean, but a later inspection finds an undelivered
    # digest — e.g. a retry that failed after the run recorded its counts.
    RunLog.objects.create(date=DATE, status="success", trigger="scheduled",
                          matches=1, enriched=1, digests=1, digests_sent=1)
    from accounts.models import Workspace
    from digests.models import Digest
    from watches.models import Client
    ws = Workspace.objects.create(name="Acme")
    c = Client.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    Digest.objects.create(client=c, date=DATE, body="b", sent=False)

    with pytest.raises(CommandError) as excinfo:
        call_command("check_heartbeat", "--date", DATE.isoformat())
    assert "undelivered" in str(excinfo.value)


@pytest.mark.django_db
def test_heartbeat_fails_when_no_run_happened():
    with pytest.raises(CommandError):
        call_command("check_heartbeat", "--date", DATE.isoformat())
