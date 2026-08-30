import datetime

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Membership, Workspace
from digests.email import FakeEmailSender
from digests.models import Digest
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from watches.models import Client as WatchClient
from watches.models import Watch

User = get_user_model()
DATE = datetime.date(2026, 7, 1)


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


@pytest.fixture
def matched_client(firm_a):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    Watch.objects.create(client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}])
    edition = ingest_edition(RawEdition(
        date=DATE, section="DO1", source_url="https://x.test/s1",
        items=(RawItem("a1", "Portaria 1", "Org", "Licença à BETA CORP.", "#a1"),),
    ))
    match_edition(edition)
    return client, user


@pytest.mark.django_db
def test_send_digest_returns_and_marks_sent(matched_client, monkeypatch):
    client, user = matched_client
    sender = FakeEmailSender()
    monkeypatch.setattr("digests.api.get_email_sender", lambda: sender)
    api = APIClient()
    api.force_authenticate(user=user)

    resp = api.post("/api/digests/send", {"client": client.id, "date": "2026-07-01"}, format="json")

    assert resp.status_code == 200
    assert resp.data["sent"] is True
    assert len(sender.sent) == 1


@pytest.mark.django_db
def test_send_digest_404s_for_a_client_outside_the_callers_workspace(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    b_client = WatchClient.objects.create(workspace=ws_b, name="B-client")
    api = APIClient()
    api.force_authenticate(user=user_a)
    resp = api.post("/api/digests/send", {"client": b_client.id, "date": "2026-07-01"}, format="json")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_send_digest_404s_when_that_date_published_nothing(firm_a):
    # Since decision-007 an empty result means the DOU did not publish, not
    # "nothing matched" -- a client with a live watch now gets a quiet digest
    # instead. No edition is ingested here, so there is genuinely nothing.
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    Watch.objects.create(client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}])
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post("/api/digests/send", {"client": client.id, "date": "2026-07-01"}, format="json")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_send_digest_sends_a_quiet_digest_when_nothing_matched(firm_a, monkeypatch):
    ws, user = firm_a
    client = WatchClient.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "nao aparece", "kind": "entity"}]}])
    ingest_edition(RawEdition(
        date=DATE, section="DO1", source_url="https://x.test/quiet",
        items=(RawItem("q1", "Portaria 9", "Org", "Assunto irrelevante.", "#q1"),),
    ))
    sender = FakeEmailSender()
    monkeypatch.setattr("digests.api.get_email_sender", lambda: sender)
    api = APIClient()
    api.force_authenticate(user=user)

    resp = api.post("/api/digests/send", {"client": client.id, "date": "2026-07-01"}, format="json")

    assert resp.status_code == 200
    assert resp.data["sent"] is True
    assert "não encontraram nada" in resp.data["body"]
    assert len(sender.sent) == 1


@pytest.mark.django_db
def test_send_digest_is_idempotent_on_resend(matched_client, monkeypatch):
    client, user = matched_client
    sender = FakeEmailSender()
    monkeypatch.setattr("digests.api.get_email_sender", lambda: sender)
    api = APIClient()
    api.force_authenticate(user=user)

    api.post("/api/digests/send", {"client": client.id, "date": "2026-07-01"}, format="json")
    api.post("/api/digests/send", {"client": client.id, "date": "2026-07-01"}, format="json")

    assert len(sender.sent) == 1
    assert Digest.objects.count() == 1
