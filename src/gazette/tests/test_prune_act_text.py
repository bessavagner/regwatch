import datetime

import pytest
from django.core.management import call_command
from django.utils import timezone

from accounts.models import Workspace
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from gazette.models import Act, Edition
from matching.matcher import match_edition
from matching.models import Match
from watches.models import Client, Watch


def _edition(date, *, items):
    return ingest_edition(RawEdition(
        date=date, section="1", source_url="https://x.test/s1", items=items,
    ))


@pytest.fixture
def aged(db):
    """One old edition: one act a watch matched, one act nothing matched."""
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta", email="b@example.test")
    Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}]
    )
    old = timezone.localdate() - datetime.timedelta(days=30)
    edition = _edition(old, items=(
        RawItem("a1", "Portaria 12", "Org", "Licença à BETA CORP.", "#a1"),
        RawItem("a2", "Portaria 13", "Org", "Nada de interesse aqui.", "#a2"),
    ))
    match_edition(edition)
    assert Match.objects.count() == 1
    return edition


@pytest.mark.django_db
def test_dry_run_reports_but_writes_nothing(aged, capsys):
    call_command("prune_act_text", "--days", "7")
    assert Act.objects.count() == 2
    assert Act.objects.exclude(raw_text="").count() == 2
    out = capsys.readouterr().out
    assert "delete (never matched): 1" in out
    assert "strip  (has matches)  : 1" in out
    assert "dry run" in out


@pytest.mark.django_db
def test_apply_deletes_unmatched_and_strips_matched(aged):
    call_command("prune_act_text", "--days", "7", "--apply")

    assert not Act.objects.filter(identifier="a2").exists()
    kept = Act.objects.get(identifier="a1")
    assert kept.raw_text == ""
    assert kept.search_text == ""
    assert kept.search_vector_pt is None
    # The identity the feed renders survives.
    assert kept.title == "Portaria 12"
    assert kept.source_anchor == "#a1"


@pytest.mark.django_db
def test_match_history_survives_the_prune(aged):
    call_command("prune_act_text", "--days", "7", "--apply")
    match = Match.objects.get()
    assert match.snippet.startswith("Licença à BETA CORP.")
    assert match.act.identifier == "a1"


@pytest.mark.django_db
def test_acts_inside_the_window_are_untouched(db):
    recent = timezone.localdate() - datetime.timedelta(days=2)
    _edition(recent, items=(RawItem("r1", "Portaria 99", "Org", "Texto recente.", "#r1"),))

    call_command("prune_act_text", "--days", "7", "--apply")

    act = Act.objects.get(identifier="r1")
    assert act.raw_text == "Texto recente."
    assert act.search_vector_pt is not None
    assert Edition.objects.get(date=recent).text_pruned_at is None


@pytest.mark.django_db
def test_pruned_edition_is_marked(aged):
    call_command("prune_act_text", "--days", "7", "--apply")
    assert Edition.objects.get(pk=aged.pk).text_pruned_at is not None


@pytest.mark.django_db
def test_reingest_restores_text_and_clears_the_mark(aged):
    call_command("prune_act_text", "--days", "7", "--apply")

    edition = _edition(aged.date, items=(
        RawItem("a1", "Portaria 12", "Org", "Licença à BETA CORP.", "#a1"),
    ))

    assert edition.pk == aged.pk
    assert edition.text_pruned_at is None
    restored = Act.objects.get(identifier="a1")
    assert restored.raw_text == "Licença à BETA CORP."
    assert restored.search_vector_pt is not None


@pytest.mark.django_db
def test_rerun_is_idempotent(aged, capsys):
    call_command("prune_act_text", "--days", "7", "--apply")
    capsys.readouterr()
    call_command("prune_act_text", "--days", "7", "--apply")
    out = capsys.readouterr().out
    assert "deleted 0, stripped 0" in out
