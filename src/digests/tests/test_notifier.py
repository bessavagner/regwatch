import datetime
from dataclasses import dataclass, field

import pytest
from accounts.models import Workspace
from watches.models import Client, Watch
from gazette.contracts import RawEdition, RawItem
from gazette.models import Act
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from matching.models import Match
from digests.email import FakeEmailSender, RaisingEmailSender
from digests.notifier import build_and_send_digests, deliver_digest
from digests.models import Digest

DATE = datetime.date(2026, 6, 26)


@pytest.fixture
def matched(db):
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta", email="beta@example.test")
    Watch.objects.create(client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}])
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
    Watch.objects.create(client=client_a, groups=[{"terms": [{"text": "alpha ltd", "kind": "entity"}]}])
    Watch.objects.create(client=client_b, groups=[{"terms": [{"text": "gamma corp", "kind": "entity"}]}])
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
    Watch.objects.create(client=client_a, groups=[{"terms": [{"text": "alpha ltd", "kind": "entity"}]}])
    Watch.objects.create(client=client_b, groups=[{"terms": [{"text": "gamma corp", "kind": "entity"}]}])
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


@dataclass
class _PartlyFailingSender:
    """Rejects one recipient the way Resend rejects an unverified sender."""

    failing: str
    sent: list[tuple[str, str, str]] = field(default_factory=list)

    def send(self, to: str, subject: str, body: str) -> None:
        if to == self.failing:
            raise RuntimeError(f"403 Forbidden for {to}")
        self.sent.append((to, subject, body))


@pytest.mark.django_db
def test_a_failing_send_does_not_block_the_other_clients(db):
    """One rejected recipient used to abort the whole pipeline run after the
    scrape and matching had already succeeded."""
    ws = Workspace.objects.create(name="PartialWS")
    client_a = Client.objects.create(workspace=ws, name="AlphaClient", email="alpha@example.test")
    client_b = Client.objects.create(workspace=ws, name="GammaClient", email="gamma@example.test")
    Watch.objects.create(client=client_a, groups=[{"terms": [{"text": "alpha ltd", "kind": "entity"}]}])
    Watch.objects.create(client=client_b, groups=[{"terms": [{"text": "gamma corp", "kind": "entity"}]}])
    edition = ingest_edition(RawEdition(
        date=DATE, section="1", source_url="https://x.test/partial",
        items=(
            RawItem("p1", "Portaria 1", "Org", "Licença à ALPHA LTD.", "#p1"),
            RawItem("p2", "Portaria 2", "Org", "Licença à GAMMA CORP.", "#p2"),
        ),
    ))
    match_edition(edition)

    sender = _PartlyFailingSender(failing="alpha@example.test")
    digests = build_and_send_digests(DATE, sender)

    # Both digests are still built and returned; the healthy one is delivered.
    assert len(digests) == 2
    assert [s[0] for s in sender.sent] == ["gamma@example.test"]

    by_client = {d.client_id: d for d in digests}
    assert by_client[client_b.pk].sent is True
    assert by_client[client_a.pk].sent is False  # stays unsent, so a retry can pick it up


@pytest.mark.django_db
def test_a_failed_send_is_retried_on_the_next_run(db):
    ws = Workspace.objects.create(name="RetryWS")
    client_a = Client.objects.create(workspace=ws, name="AlphaClient", email="alpha@example.test")
    Watch.objects.create(client=client_a, groups=[{"terms": [{"text": "alpha ltd", "kind": "entity"}]}])
    edition = ingest_edition(RawEdition(
        date=DATE, section="1", source_url="https://x.test/retry",
        items=(RawItem("r1", "Portaria 1", "Org", "Licença à ALPHA LTD.", "#r1"),),
    ))
    match_edition(edition)

    build_and_send_digests(DATE, _PartlyFailingSender(failing="alpha@example.test"))

    recovered = FakeEmailSender()
    digests = build_and_send_digests(DATE, recovered)

    assert len(recovered.sent) == 1
    assert digests[0].sent is True


@pytest.mark.django_db
def test_failed_send_records_the_reason_on_the_digest(matched):
    digests = build_and_send_digests(DATE, RaisingEmailSender("mailbox full"))
    digest = digests[0]
    digest.refresh_from_db()
    assert digest.sent is False
    assert "mailbox full" in digest.send_error
    assert digest.send_attempts == 1
    assert digest.last_attempt_at is not None


@pytest.mark.django_db
def test_successful_send_clears_a_previous_error(matched):
    build_and_send_digests(DATE, RaisingEmailSender("temporary"))
    digest = Digest.objects.get(client=matched, date=DATE)
    assert digest.send_error

    sent = deliver_digest(digest, FakeEmailSender())

    digest.refresh_from_db()
    assert sent is True
    assert digest.sent is True
    assert digest.send_error == ""
    assert digest.send_attempts == 2


@pytest.mark.django_db
def test_deliver_digest_skips_a_client_with_no_email(matched):
    matched.email = ""
    matched.save()
    digest = Digest.objects.create(client=matched, date=DATE, body="x")

    assert deliver_digest(digest, FakeEmailSender()) is False
    digest.refresh_from_db()
    assert digest.sent is False
    assert "no email address" in digest.send_error


@pytest.mark.django_db
def test_unenriched_match_says_the_summary_is_missing(matched):
    build_and_send_digests(DATE, FakeEmailSender())
    body = Digest.objects.get(client=matched, date=DATE).body
    # The match was never enriched, so category is "" and ai_summary is None.
    assert "[sem categoria]" not in body
    assert "[resumo indisponível]" in body


@pytest.mark.django_db
def test_digest_links_every_item_to_the_dou(matched):
    act = Act.objects.get()
    act.source_anchor = (
        "http://pesquisa.in.gov.br/imprensa/jsp/visualiza/index.jsp"
        "?data=26/06/2026&jornal=515&pagina=19"
    )
    act.save(update_fields=["source_anchor"])
    sender = FakeEmailSender()
    body = build_and_send_digests(DATE, sender)[0].body
    assert act.dou_url in body
    # Plain-text mail: the ampersands have to survive as themselves. Django
    # autoescapes .txt templates too, which would ship &amp; in the query string
    # and break the link in every client that does not un-escape it.
    assert "&amp;" not in body


@pytest.mark.django_db
def test_digest_links_an_act_that_has_no_anchor(matched):
    Act.objects.update(source_anchor="")
    sender = FakeEmailSender()
    body = build_and_send_digests(DATE, sender)[0].body
    assert "https://www.in.gov.br/leiturajornal?data=26-06-2026&secao=do1" in body


@pytest.mark.django_db
def test_digest_header_carries_a_brazilian_date(matched):
    sender = FakeEmailSender()
    body = build_and_send_digests(DATE, sender)[0].body
    assert "26 de junho de 2026" in body


@pytest.mark.django_db
def test_digest_subject_carries_a_brazilian_date(matched):
    sender = FakeEmailSender()
    build_and_send_digests(DATE, sender)
    subject = sender.sent[0][1]      # (to, subject, body)
    assert subject == "RegWatch — 26 de junho de 2026"


def _client_with_watch(name="Beta"):
    ws = Workspace.objects.create(name=f"WS {name}")
    client = Client.objects.create(workspace=ws, name=name, email=f"{name}@example.test")
    Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    return client


@pytest.mark.django_db
def test_digest_leads_with_the_highest_ranked_match():
    _client_with_watch()
    edition = ingest_edition(RawEdition(
        date=DATE, section="DO1", source_url="https://x.test/s1",
        items=(
            RawItem("a1", "Autorizacao rotineira", "Org", "Autorização à BETA CORP.", "#a1"),
            RawItem("a2", "Revisao tarifaria", "Org", "Revisão tarifária da BETA CORP.", "#a2"),
        ),
    ))
    match_edition(edition)
    # rank is advisory and comes from the tsvector; pin it so this test is about
    # ordering rather than about what the matcher happened to score.
    Match.objects.filter(act__identifier="a1").update(rank=0.1)
    Match.objects.filter(act__identifier="a2").update(rank=0.9)

    body = build_and_send_digests(DATE, FakeEmailSender())[0].body
    assert body.index("Revisao tarifaria") < body.index("Autorizacao rotineira")


@pytest.mark.django_db
def test_matches_of_equal_rank_are_ordered_by_section():
    _client_with_watch()
    for section, identifier, title in (
        ("DO2", "b1", "Ato da segunda secao"),
        ("DO1", "a1", "Ato da primeira secao"),
    ):
        edition = ingest_edition(RawEdition(
            date=DATE, section=section, source_url=f"https://x.test/{section}",
            items=(RawItem(identifier, title, "Org", "Licença à BETA CORP.", f"#{identifier}"),),
        ))
        match_edition(edition)
    Match.objects.update(rank=0.5)

    body = build_and_send_digests(DATE, FakeEmailSender())[0].body
    assert body.index("Ato da primeira secao") < body.index("Ato da segunda secao")
