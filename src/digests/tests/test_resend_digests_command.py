import datetime

import pytest
from django.core.management import call_command

from accounts.models import Workspace
from digests.email import FakeEmailSender, RaisingEmailSender
from digests.models import Digest
from digests.notifier import retry_unsent_digests
from watches.models import Client

DATE = datetime.date(2026, 8, 5)


@pytest.fixture
def unsent(db):
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    for offset in range(3):
        Digest.objects.create(
            client=client, date=DATE + datetime.timedelta(days=offset),
            body="body", sent=False,
        )
    return client


@pytest.mark.django_db
def test_retry_sends_every_unsent_digest_in_the_window(unsent):
    sender = FakeEmailSender()
    sent, attempted = retry_unsent_digests(DATE, DATE + datetime.timedelta(days=2), sender)
    assert (sent, attempted) == (3, 3)
    assert Digest.objects.filter(sent=True).count() == 3


@pytest.mark.django_db
def test_retry_ignores_digests_outside_the_window(unsent):
    sender = FakeEmailSender()
    sent, attempted = retry_unsent_digests(DATE, DATE, sender)
    assert (sent, attempted) == (1, 1)
    assert Digest.objects.filter(sent=True).count() == 1


@pytest.mark.django_db
def test_retry_reports_failures_without_raising(unsent):
    sent, attempted = retry_unsent_digests(
        DATE, DATE + datetime.timedelta(days=2), RaisingEmailSender("still broken")
    )
    assert (sent, attempted) == (0, 3)
    assert Digest.objects.filter(sent=True).count() == 0
    assert "still broken" in Digest.objects.first().send_error


@pytest.mark.django_db
def test_command_uses_the_configured_sender(unsent, monkeypatch, capsys):
    sender = FakeEmailSender()
    monkeypatch.setattr(
        "digests.management.commands.resend_digests.get_email_sender", lambda: sender
    )
    call_command("resend_digests", "--date-from", "2026-08-05", "--date-to", "2026-08-07")
    assert len(sender.sent) == 3
    assert "resent 3 of 3" in capsys.readouterr().out
