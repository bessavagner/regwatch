import pytest
from accounts.models import Workspace
from watches.models import Client, Watch


@pytest.mark.django_db
def test_watch_belongs_to_client():
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta Corp")
    watch = Watch.objects.create(client=client, terms=["beta corp"], exclude=["revogado"])
    assert watch.active is True
    assert watch.client.workspace == ws
    assert watch.terms == ["beta corp"]
