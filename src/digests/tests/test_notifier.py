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
    client = Client.objects.create(workspace=ws, name="Beta")
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
def test_digests_are_idempotent(matched):
    sender = FakeEmailSender()
    build_and_send_digests(DATE, sender)
    build_and_send_digests(DATE, sender)
    assert Digest.objects.count() == 1
