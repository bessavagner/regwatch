import datetime

import pytest
from django.core.management import call_command

from accounts.models import Workspace
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from matching.models import Match
from watches.models import Client, Watch

DATE = datetime.date(2026, 6, 26)


@pytest.fixture
def stale(db):
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta", email="b@example.test")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    edition = ingest_edition(RawEdition(
        date=DATE, section="1", source_url="https://x.test/s1",
        items=(RawItem("a1", "Portaria 12", "Org", "Licença à BETA CORP.", "#a1"),),
    ))
    match_edition(edition)
    # The watch is retargeted; its existing match no longer satisfies it.
    watch.groups = [{"terms": [{"text": "gamma industries", "kind": "entity"}]}]
    watch.save()
    return watch


@pytest.mark.django_db
def test_dry_run_reports_but_deletes_nothing(stale, capsys):
    call_command("prune_stale_matches")
    assert Match.objects.count() == 1
    out = capsys.readouterr().out
    assert "would delete 1" in out


@pytest.mark.django_db
def test_apply_deletes_the_stale_match(stale):
    call_command("prune_stale_matches", "--apply")
    assert Match.objects.count() == 0


@pytest.mark.django_db
def test_a_still_valid_match_is_kept(stale):
    stale.groups = [{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    stale.save()
    call_command("prune_stale_matches", "--apply")
    assert Match.objects.count() == 1


@pytest.mark.django_db
def test_a_triaged_match_is_never_deleted(stale):
    Match.objects.update(state="relevant")
    call_command("prune_stale_matches", "--apply")
    assert Match.objects.count() == 1, "a human verdict is not ours to discard"
