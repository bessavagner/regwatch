from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import Workspace
from watches.models import Client, Watch


@pytest.fixture
def watch(db):
    ws = Workspace.objects.create(name="UW")
    client = Client.objects.create(workspace=ws, name="Cactarus")
    return Watch.objects.create(
        client=client,
        groups=[{"terms": [{"text": "Pentecoste", "kind": "entity"}]}],
        exclude=["velho"], section="DO1",
    )


def _call(*args):
    out = StringIO()
    call_command("update_watch", *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_it_is_a_dry_run_unless_apply_is_given(watch):
    out = _call("--watch", str(watch.pk), "--groups", "entity:Crateús")
    watch.refresh_from_db()
    assert watch.groups == [{"terms": [{"text": "Pentecoste", "kind": "entity"}]}]
    assert "dry run" in out


@pytest.mark.django_db
def test_the_dry_run_shows_before_and_after(watch):
    # A mutation you cannot preview is a mutation you apply blind.
    out = _call("--watch", str(watch.pk), "--groups", "entity:Crateús")
    assert "Pentecoste" in out and "Crateús" in out
    assert "before" in out and "after" in out


@pytest.mark.django_db
def test_apply_replaces_the_groups(watch):
    _call("--watch", str(watch.pk), "--groups", "entity:Crateús|Ipueiras", "--apply")
    watch.refresh_from_db()
    assert watch.groups == [{"terms": [
        {"text": "Crateús", "kind": "entity"}, {"text": "Ipueiras", "kind": "entity"},
    ]}]
    # untouched fields stay put
    assert watch.exclude == ["velho"]
    assert watch.section == "DO1"


@pytest.mark.django_db
def test_excludes_are_replaced_only_when_given(watch):
    _call("--watch", str(watch.pk), "--excludes", "novo;outro", "--apply")
    watch.refresh_from_db()
    assert watch.exclude == ["novo", "outro"]
    assert watch.groups == [{"terms": [{"text": "Pentecoste", "kind": "entity"}]}]


@pytest.mark.django_db
def test_excludes_can_be_emptied_explicitly(watch):
    _call("--watch", str(watch.pk), "--clear-excludes", "--apply")
    watch.refresh_from_db()
    assert watch.exclude == []


@pytest.mark.django_db
def test_a_watch_can_be_deactivated(watch):
    _call("--watch", str(watch.pk), "--inactive", "--apply")
    watch.refresh_from_db()
    assert watch.active is False


@pytest.mark.django_db
def test_an_update_that_changes_nothing_is_an_error(watch):
    with pytest.raises(CommandError, match="nothing to change"):
        _call("--watch", str(watch.pk), "--apply")


@pytest.mark.django_db
def test_an_unknown_watch_is_an_error(watch):
    with pytest.raises(CommandError, match="no watch"):
        _call("--watch", "99999", "--groups", "entity:x", "--apply")


@pytest.mark.django_db
def test_a_bad_kind_is_rejected(watch):
    with pytest.raises(CommandError, match="kind"):
        _call("--watch", str(watch.pk), "--groups", "banana:x", "--apply")
