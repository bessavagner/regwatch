import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Membership, Workspace

User = get_user_model()


@pytest.fixture
def user_in_workspace(db):
    ws = Workspace.objects.create(name="Acme")
    user = User.objects.create_user(username="a@firm.com", email="a@firm.com", password="pw12345")
    Membership.objects.create(workspace=ws, user=user)
    return user, ws


@pytest.mark.django_db
def test_login_returns_me_payload(user_in_workspace):
    user, ws = user_in_workspace
    client = APIClient()
    resp = client.post("/api/auth/login", {"username": "a@firm.com", "password": "pw12345"})
    assert resp.status_code == 200
    assert resp.data["username"] == "a@firm.com"
    assert resp.data["workspace"]["name"] == "Acme"


@pytest.mark.django_db
def test_login_rejects_bad_credentials(user_in_workspace):
    client = APIClient()
    resp = client.post("/api/auth/login", {"username": "a@firm.com", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.django_db
def test_me_requires_authentication(db):
    client = APIClient()
    assert client.get("/api/me").status_code == 403


@pytest.mark.django_db
def test_me_returns_workspace_when_authenticated(user_in_workspace):
    user, ws = user_in_workspace
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get("/api/me")
    assert resp.status_code == 200
    assert resp.data["workspace"]["id"] == ws.id


@pytest.mark.django_db
def test_logout_requires_authentication(db):
    client = APIClient()
    assert client.post("/api/auth/logout").status_code == 403


@pytest.mark.django_db
def test_logout_ends_session(user_in_workspace):
    client = APIClient()
    login = client.post(
        "/api/auth/login", {"username": "a@firm.com", "password": "pw12345"}
    )
    assert login.status_code == 200
    assert client.get("/api/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/me").status_code == 403
