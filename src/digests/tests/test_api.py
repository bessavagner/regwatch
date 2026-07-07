import datetime

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Membership, Workspace
from digests.models import Digest
from watches.models import Client as WatchClient

User = get_user_model()


def _member(name, email):
    ws = Workspace.objects.create(name=name)
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
def test_digest_list_scoped_and_ordered(firm_a):
    ws, user = firm_a
    c = WatchClient.objects.create(workspace=ws, name="C")
    Digest.objects.create(client=c, date=datetime.date(2026, 7, 1), body="old", sent=True)
    Digest.objects.create(client=c, date=datetime.date(2026, 7, 2), body="new", sent=True)
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.get("/api/digests")
    assert resp.status_code == 200
    assert [d["body"] for d in resp.data["results"]] == ["new", "old"]


@pytest.mark.django_db
def test_cannot_read_other_workspace_digest(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    c_b = WatchClient.objects.create(workspace=ws_b, name="B")
    d_b = Digest.objects.create(client=c_b, date=datetime.date(2026, 7, 1), body="b", sent=True)
    api = APIClient()
    api.force_authenticate(user=user_a)
    assert api.get("/api/digests").data["count"] == 0
    assert api.get(f"/api/digests/{d_b.id}").status_code == 404
