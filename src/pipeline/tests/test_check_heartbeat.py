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
