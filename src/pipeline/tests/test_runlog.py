import pytest
from pipeline.models import RunLog


@pytest.mark.django_db
def test_runlog_defaults_and_persists():
    log = RunLog.objects.create(date="2026-06-26")
    assert log.status == "running"
    assert log.trigger == "scheduled"
    assert log.editions == 0 and log.acts == 0 and log.matches == 0
    assert log.enriched == 0 and log.digests == 0
    assert log.errors == ""
    assert log.started_at is not None
    assert log.finished_at is None

    log.status = "success"
    log.acts = 400
    log.save()
    assert RunLog.objects.get(pk=log.pk).acts == 400


@pytest.mark.django_db
def test_runlog_trigger_can_be_set_to_backfill():
    log = RunLog.objects.create(date="2026-06-26", trigger="backfill")
    assert log.trigger == "backfill"
