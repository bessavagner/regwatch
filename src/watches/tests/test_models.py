from importlib import import_module

import pytest
from accounts.models import Workspace
from django.apps import apps as real_apps
from watches.models import Client, Watch

backfill_watch_groups = import_module("watches.migrations.0005_backfill_watch_groups")


@pytest.mark.django_db
def test_watch_belongs_to_client():
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta Corp")
    watch = Watch.objects.create(client=client, terms=["beta corp"], exclude=["revogado"])
    assert watch.active is True
    assert watch.client.workspace == ws
    assert watch.terms == ["beta corp"]


@pytest.mark.django_db
def test_watch_groups_defaults_to_empty_list():
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta")
    watch = Watch.objects.create(client=client, terms=["beta corp"])
    watch.refresh_from_db()
    assert watch.groups == []


@pytest.mark.django_db
def test_watch_stores_a_groups_structure():
    ws = Workspace.objects.create(name="Acme2")
    client = Client.objects.create(workspace=ws, name="Beta2")
    groups = [{"terms": [{"text": "sebrae", "kind": "entity"}]}]
    watch = Watch.objects.create(client=client, terms=[], groups=groups)
    watch.refresh_from_db()
    assert watch.groups == groups


@pytest.mark.django_db
def test_0005_backfill_converts_all_mode_to_one_group_per_term():
    ws = Workspace.objects.create(name="Acme3")
    client = Client.objects.create(workspace=ws, name="Beta3")
    watch = Watch.objects.create(
        client=client, terms=["alpha", "beta"], match_mode="all"
    )

    backfill_watch_groups.forwards(real_apps, None)

    watch.refresh_from_db()
    assert watch.groups == [
        {"terms": [{"text": "alpha", "kind": "entity"}]},
        {"terms": [{"text": "beta", "kind": "entity"}]},
    ]


@pytest.mark.django_db
def test_0005_backfill_converts_any_mode_to_one_group_with_both_terms():
    ws = Workspace.objects.create(name="Acme4")
    client = Client.objects.create(workspace=ws, name="Beta4")
    watch = Watch.objects.create(
        client=client, terms=["alpha", "beta"], match_mode="any"
    )

    backfill_watch_groups.forwards(real_apps, None)

    watch.refresh_from_db()
    assert watch.groups == [
        {
            "terms": [
                {"text": "alpha", "kind": "entity"},
                {"text": "beta", "kind": "entity"},
            ]
        }
    ]


@pytest.mark.django_db
def test_0005_backfill_leaves_a_termless_watch_inert():
    ws = Workspace.objects.create(name="Acme5")
    client = Client.objects.create(workspace=ws, name="Beta5")
    watch = Watch.objects.create(client=client, terms=[], match_mode="all")

    backfill_watch_groups.forwards(real_apps, None)

    watch.refresh_from_db()
    assert watch.groups == []


@pytest.mark.django_db
def test_0005_backwards_resets_groups_to_empty_list():
    ws = Workspace.objects.create(name="Acme6")
    client = Client.objects.create(workspace=ws, name="Beta6")
    groups = [{"terms": [{"text": "alpha", "kind": "entity"}]}]
    watch = Watch.objects.create(
        client=client, terms=["alpha"], match_mode="all", groups=groups
    )

    backfill_watch_groups.backwards(real_apps, None)

    watch.refresh_from_db()
    assert watch.groups == []
