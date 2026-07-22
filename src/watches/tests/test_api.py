import datetime

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Membership, Workspace
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from watches.models import Client as WatchClient
from watches.models import Watch

User = get_user_model()


def _member(workspace_name, email):
    ws = Workspace.objects.create(name=workspace_name)
    user = User.objects.create_user(username=email, email=email, password="pw12345")
    Membership.objects.create(workspace=ws, user=user)
    return ws, user


def _client_for(firm, name="Beta"):
    ws, _ = firm
    return WatchClient.objects.create(workspace=ws, name=name)


def _api_for(firm):
    _, user = firm
    api = APIClient()
    api.force_authenticate(user=user)
    return api


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
def test_cannot_read_other_workspace_watch(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    b_client = WatchClient.objects.create(workspace=ws_b, name="B-client")
    b_watch = Watch.objects.create(client=b_client, terms=["x"])
    api = APIClient()
    api.force_authenticate(user=user_a)
    assert api.get(f"/api/watches/{b_watch.id}").status_code == 404


@pytest.mark.django_db
def test_create_client_without_membership_is_forbidden(db):
    user = User.objects.create_user(
        username="orphan@x.com", email="orphan@x.com", password="pw12345"
    )
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post("/api/clients", {"name": "X"}, format="json")
    assert resp.status_code == 403
    assert WatchClient.objects.count() == 0


@pytest.mark.django_db
def test_watch_requires_groups(firm_a):
    c = _client_for(firm_a)
    api = _api_for(firm_a)
    resp = api.post("/api/watches", {"client": c.id}, format="json")
    assert resp.status_code == 400
    assert "groups" in resp.data
    assert Watch.objects.count() == 0


@pytest.mark.django_db
def test_watch_is_created_with_groups(firm_a):
    c = _client_for(firm_a)
    api = _api_for(firm_a)
    resp = api.post("/api/watches", {
        "client": c.id,
        "groups": [{"terms": [{"text": "sebrae", "kind": "entity"}]}],
    }, format="json")
    assert resp.status_code == 201
    assert resp.data["groups"] == [{"terms": [{"text": "sebrae", "kind": "entity"}]}]


@pytest.mark.django_db
def test_watch_defaults_term_kind_to_entity(firm_a):
    c = _client_for(firm_a)
    api = _api_for(firm_a)
    resp = api.post("/api/watches", {
        "client": c.id, "groups": [{"terms": [{"text": "sebrae"}]}],
    }, format="json")
    assert resp.status_code == 201
    assert resp.data["groups"][0]["terms"][0]["kind"] == "entity"


@pytest.mark.django_db
def test_watch_rejects_empty_groups(firm_a):
    c = _client_for(firm_a)
    api = _api_for(firm_a)
    resp = api.post("/api/watches", {"client": c.id, "groups": []}, format="json")
    assert resp.status_code == 400
    assert "groups" in resp.data


@pytest.mark.django_db
def test_watch_rejects_a_group_with_no_terms(firm_a):
    c = _client_for(firm_a)
    api = _api_for(firm_a)
    resp = api.post("/api/watches", {
        "client": c.id, "groups": [{"terms": []}],
    }, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_watch_rejects_an_invalid_kind(firm_a):
    c = _client_for(firm_a)
    api = _api_for(firm_a)
    resp = api.post("/api/watches", {
        "client": c.id, "groups": [{"terms": [{"text": "x", "kind": "bogus"}]}],
    }, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_watch_rejects_non_string_term_text(firm_a):
    c = _client_for(firm_a)
    api = _api_for(firm_a)
    resp = api.post("/api/watches", {
        "client": c.id, "groups": [{"terms": [{"text": 123, "kind": "entity"}]}],
    }, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_watch_created_via_api_actually_matches(firm_a):
    # Regression guard for the 2026-07-21 production bug: a watch created through
    # the live API must produce real matches, not just accept the POST. Before this
    # task, WatchSerializer ignored `groups` entirely and every API-created watch
    # matched nothing, silently.
    c = _client_for(firm_a)
    api = _api_for(firm_a)
    resp = api.post("/api/watches", {
        "client": c.id,
        "groups": [{"terms": [{"text": "sebrae", "kind": "entity"}]}],
    }, format="json")
    assert resp.status_code == 201

    edition = ingest_edition(RawEdition(
        date=datetime.date(2026, 6, 26), section="1",
        source_url="https://example.test/s1",
        items=(RawItem("a1", "Ato", "Org", "Convenio com o SEBRAE nesta data.", "#a1"),),
    ))
    matches = match_edition(edition)
    assert len(matches) == 1
    assert matches[0].watch_id == resp.data["id"]


@pytest.mark.django_db
def test_watch_cannot_attach_to_other_workspace_client(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    b_client = WatchClient.objects.create(workspace=ws_b, name="B-client")
    api = APIClient()
    api.force_authenticate(user=user_a)
    resp = api.post("/api/watches", {
        "client": b_client.id,
        "groups": [{"terms": [{"text": "x", "kind": "entity"}]}],
    }, format="json")
    assert resp.status_code == 400
    assert "client" in resp.data
