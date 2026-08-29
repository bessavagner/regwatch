import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import Workspace
from watches.models import Client, Watch


@pytest.fixture
def client(db):
    ws = Workspace.objects.create(name="CW")
    return Client.objects.create(workspace=ws, name="Cactarus")


def _call(*args, **kwargs):
    out = StringIO()
    call_command("create_watch", *args, stdout=out, **kwargs)
    return out.getvalue()


@pytest.mark.django_db
def test_it_is_a_dry_run_unless_apply_is_given(client):
    out = _call("--client", str(client.pk), "--group", "entity:Pentecoste|Coreaú")
    assert Watch.objects.count() == 0
    assert "dry run" in out


@pytest.mark.django_db
def test_apply_creates_the_watch_with_grouped_terms(client):
    _call(
        "--client", str(client.pk),
        "--group", "entity:Pentecoste|Coreaú",
        "--group", "concept:convênio|termo de fomento",
        "--exclude", "aviso de licitacao",
        "--section", "DO1",
        "--apply",
    )
    watch = Watch.objects.get()
    assert watch.client == client
    assert watch.groups == [
        {"terms": [
            {"text": "Pentecoste", "kind": "entity"},
            {"text": "Coreaú", "kind": "entity"},
        ]},
        {"terms": [
            {"text": "convênio", "kind": "concept"},
            {"text": "termo de fomento", "kind": "concept"},
        ]},
    ]
    assert watch.exclude == ["aviso de licitacao"]
    assert watch.section == "DO1"
    assert watch.active is True


@pytest.mark.django_db
def test_a_group_without_a_kind_prefix_defaults_to_entity(client):
    _call("--client", str(client.pk), "--group", "Pentecoste", "--apply")
    assert Watch.objects.get().groups == [
        {"terms": [{"text": "Pentecoste", "kind": "entity"}]}
    ]


@pytest.mark.django_db
def test_it_refuses_to_create_a_duplicate_of_an_existing_watch(client):
    args = ("--client", str(client.pk), "--group", "entity:Pentecoste", "--section", "DO1")
    _call(*args, "--apply")
    with pytest.raises(CommandError, match="identical"):
        _call(*args, "--apply")
    assert Watch.objects.count() == 1


@pytest.mark.django_db
def test_an_unknown_client_is_an_error_not_a_silent_no_op(client):
    with pytest.raises(CommandError, match="no client"):
        _call("--client", "99999", "--group", "entity:x", "--apply")


@pytest.mark.django_db
def test_a_group_with_no_usable_terms_is_rejected(client):
    # matcher.py fails closed on an empty group -- the watch would match nothing
    # and look active, which is the worst of both.
    with pytest.raises(CommandError, match="no terms"):
        _call("--client", str(client.pk), "--group", "concept:  |  ", "--apply")


@pytest.mark.django_db
def test_an_unknown_kind_is_rejected(client):
    with pytest.raises(CommandError, match="kind"):
        _call("--client", str(client.pk), "--group", "banana:x", "--apply")


@pytest.mark.django_db
def test_json_output_reports_the_created_id(client):
    out = _call("--client", str(client.pk), "--group", "entity:x", "--apply", "--json")
    assert json.loads(out)["id"] == Watch.objects.get().pk


@pytest.mark.django_db
def test_groups_can_arrive_as_one_semicolon_separated_argument(client):
    # `gcloud run jobs execute --args` rejects a repeated flag ("--group cannot
    # be specified multiple times"), so the production path needs a form that
    # names each flag once.
    _call(
        "--client", str(client.pk),
        "--groups", "entity:Pentecoste|Coreaú;concept:convênio|termo de fomento",
        "--excludes", "aviso de licitacao;pregao eletronico",
        "--section", "DO1", "--apply",
    )
    watch = Watch.objects.get()
    assert watch.groups == [
        {"terms": [
            {"text": "Pentecoste", "kind": "entity"},
            {"text": "Coreaú", "kind": "entity"},
        ]},
        {"terms": [
            {"text": "convênio", "kind": "concept"},
            {"text": "termo de fomento", "kind": "concept"},
        ]},
    ]
    assert watch.exclude == ["aviso de licitacao", "pregao eletronico"]


@pytest.mark.django_db
def test_the_two_group_forms_agree(client):
    out_a = _call("--client", str(client.pk), "--groups", "entity:a|b;concept:c")
    out_b = _call("--client", str(client.pk), "--group", "entity:a|b", "--group", "concept:c")
    assert out_a == out_b


@pytest.mark.django_db
def test_at_least_one_group_is_required(client):
    with pytest.raises(CommandError, match="at least one group"):
        _call("--client", str(client.pk), "--apply")
