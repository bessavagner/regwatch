import datetime
import pytest
from accounts.models import Workspace
from watches.models import Client, Watch
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from digests.email import FakeEmailSender
from digests.notifier import build_and_send_digests
from digests.models import Digest

DATE = datetime.date(2026, 6, 26)


@pytest.fixture
def matched(db):
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    Watch.objects.create(client=client, terms=["beta corp"])
    edition = ingest_edition(RawEdition(
        date=DATE, section="1", source_url="https://x.test/s1",
        items=(RawItem("a1", "Portaria 12", "Org", "Licença à BETA CORP.", "#a1"),),
    ))
    match_edition(edition)
    return client


@pytest.mark.django_db
def test_builds_one_digest_per_client_and_sends(matched):
    sender = FakeEmailSender()
    digests = build_and_send_digests(DATE, sender)
    assert len(digests) == 1
    assert digests[0].client == matched
    assert "BETA CORP" in digests[0].body
    assert digests[0].sent is True
    assert len(sender.sent) == 1


@pytest.mark.django_db
def test_digest_sends_to_client_email(matched):
    matched.email = "ops@betacorp.example"
    matched.save()
    sender = FakeEmailSender()
    build_and_send_digests(DATE, sender)
    assert len(sender.sent) == 1
    assert sender.sent[0][0] == "ops@betacorp.example"   # (to, subject, body)


@pytest.mark.django_db
def test_digest_without_email_is_built_but_not_sent(matched):
    matched.email = ""
    matched.save()
    sender = FakeEmailSender()
    digests = build_and_send_digests(DATE, sender)
    assert len(digests) == 1
    assert digests[0].sent is False
    assert sender.sent == []


@pytest.mark.django_db
def test_digests_are_idempotent(matched):
    sender = FakeEmailSender()
    build_and_send_digests(DATE, sender)
    build_and_send_digests(DATE, sender)
    assert Digest.objects.count() == 1


@pytest.mark.django_db
def test_two_clients_receive_separate_digests(db):
    """Each client gets exactly one digest containing only their own matches;
    two distinct emails are dispatched — exercising the by_client grouping loop."""
    ws = Workspace.objects.create(name="MultiWS")
    client_a = Client.objects.create(workspace=ws, name="AlphaClient", email="alpha@example.test")
    client_b = Client.objects.create(workspace=ws, name="GammaClient", email="gamma@example.test")
    Watch.objects.create(client=client_a, terms=["alpha ltd"])
    Watch.objects.create(client=client_b, terms=["gamma corp"])
    edition = ingest_edition(RawEdition(
        date=DATE, section="1", source_url="https://x.test/multi",
        items=(
            RawItem("c1", "Portaria 1", "Org", "Licença à ALPHA LTD.", "#c1"),
            RawItem("c2", "Portaria 2", "Org", "Licença à GAMMA CORP.", "#c2"),
        ),
    ))
    match_edition(edition)

    sender = FakeEmailSender()
    build_and_send_digests(DATE, sender)

    assert Digest.objects.count() == 2
    assert len(sender.sent) == 2

    digest_by_client = {d.client_id: d for d in Digest.objects.all()}
    body_a = digest_by_client[client_a.pk].body
    body_b = digest_by_client[client_b.pk].body
    assert "ALPHA LTD"  in body_a
    assert "GAMMA CORP" not in body_a
    assert "GAMMA CORP" in body_b
    assert "ALPHA LTD"  not in body_b


@pytest.mark.django_db
def test_client_filter_limits_digests_to_one_client(db):
    ws = Workspace.objects.create(name="MultiWS2")
    client_a = Client.objects.create(workspace=ws, name="AlphaClient", email="alpha@example.test")
    client_b = Client.objects.create(workspace=ws, name="GammaClient", email="gamma@example.test")
    Watch.objects.create(client=client_a, terms=["alpha ltd"])
    Watch.objects.create(client=client_b, terms=["gamma corp"])
    edition = ingest_edition(RawEdition(
        date=DATE, section="1", source_url="https://x.test/filter",
        items=(
            RawItem("f1", "Portaria 1", "Org", "Licença à ALPHA LTD.", "#f1"),
            RawItem("f2", "Portaria 2", "Org", "Licença à GAMMA CORP.", "#f2"),
        ),
    ))
    match_edition(edition)

    sender = FakeEmailSender()
    digests = build_and_send_digests(DATE, sender, client=client_a)

    assert len(digests) == 1
    assert digests[0].client == client_a
    assert len(sender.sent) == 1
    assert Digest.objects.filter(client=client_b).count() == 0


@pytest.mark.django_db
def test_client_filter_resend_is_idempotent(matched):
    sender = FakeEmailSender()
    build_and_send_digests(DATE, sender, client=matched)
    build_and_send_digests(DATE, sender, client=matched)
    assert Digest.objects.filter(client=matched).count() == 1
    assert len(sender.sent) == 1
