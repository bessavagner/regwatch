import pytest
from accounts.models import Workspace
from watches.models import Client, Watch


@pytest.mark.django_db
def test_watch_belongs_to_client():
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta Corp")
    watch = Watch.objects.create(
        client=client,
        groups=[{"terms": [{"text": "beta corp", "kind": "entity"}]}],
        exclude=["revogado"],
    )
    assert watch.active is True
    assert watch.client.workspace == ws


@pytest.mark.django_db
def test_watch_groups_defaults_to_empty_list():
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta")
    watch = Watch.objects.create(client=client)
    watch.refresh_from_db()
    assert watch.groups == []


@pytest.mark.django_db
def test_watch_stores_a_groups_structure():
    ws = Workspace.objects.create(name="Acme2")
    client = Client.objects.create(workspace=ws, name="Beta2")
    groups = [{"terms": [{"text": "sebrae", "kind": "entity"}]}]
    watch = Watch.objects.create(client=client, groups=groups)
    watch.refresh_from_db()
    assert watch.groups == groups


@pytest.mark.django_db
def test_watch_no_longer_has_legacy_fields():
    ws = Workspace.objects.create(name="LegacyWS")
    client = Client.objects.create(workspace=ws, name="Legacy")
    watch = Watch.objects.create(client=client, groups=[{"terms": [{"text": "x", "kind": "entity"}]}])
    assert not hasattr(watch, "terms")
    assert not hasattr(watch, "match_mode")
