import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Membership, Workspace
from watches.models import Client as WatchClient
from watches.models import Watch

User = get_user_model()


def _member(workspace_name, email):
    ws = Workspace.objects.create(name=workspace_name)
    user = User.objects.create_user(username=email, email=email, password="pw12345")
    Membership.objects.create(workspace=ws, user=user)
    return ws, user


@pytest.fixture
def firm_a(db):
    return _member("Firm A", "a@firm.com")


@pytest.fixture
def firm_b(db):
    return _member("Firm B", "b@firm.com")


@pytest.mark.django_db
def test_create_client_sets_callers_workspace(firm_a):
    ws, user = firm_a
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post("/api/clients", {"name": "Beta Corp"}, format="json")
    assert resp.status_code == 201
    client = WatchClient.objects.get(id=resp.data["id"])
    assert client.workspace == ws


@pytest.mark.django_db
def test_client_list_is_scoped_to_workspace(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    WatchClient.objects.create(workspace=ws_a, name="A-client")
    WatchClient.objects.create(workspace=ws_b, name="B-client")
    api = APIClient()
    api.force_authenticate(user=user_a)
    resp = api.get("/api/clients")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.data["results"]]
    assert names == ["A-client"]


@pytest.mark.django_db
def test_cannot_read_other_workspace_client(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    b_client = WatchClient.objects.create(workspace=ws_b, name="B-client")
    api = APIClient()
    api.force_authenticate(user=user_a)
    assert api.get(f"/api/clients/{b_client.id}").status_code == 404


@pytest.mark.django_db
def test_watch_requires_non_empty_terms(firm_a):
    ws, user = firm_a
    c = WatchClient.objects.create(workspace=ws, name="Beta")
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post("/api/watches", {"client": c.id, "terms": []}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_watch_cannot_attach_to_other_workspace_client(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    b_client = WatchClient.objects.create(workspace=ws_b, name="B-client")
    api = APIClient()
    api.force_authenticate(user=user_a)
    resp = api.post(
        "/api/watches", {"client": b_client.id, "terms": ["x"]}, format="json"
    )
    assert resp.status_code == 400
