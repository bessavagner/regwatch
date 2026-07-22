import datetime
import itertools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Membership, Workspace
from gazette.models import Act, Edition
from matching.models import Match
from watches.models import Client as WatchClient
from watches.models import Watch

User = get_user_model()
_seq = itertools.count()


def _member(name, email):
    ws = Workspace.objects.create(name=name)
    user = User.objects.create_user(username=email, email=email, password="pw12345")
    Membership.objects.create(workspace=ws, user=user)
    return ws, user


def _match(ws, *, section="1", date, category="", state="new", rank=0.0):
    n = next(_seq)
    client = WatchClient.objects.create(workspace=ws, name="C")
    watch = Watch.objects.create(client=client, groups=[{"terms": [{"text": "x", "kind": "entity"}]}])
    edition, _ = Edition.objects.get_or_create(
        date=date, section=section, defaults={"source_url": "https://e.test"}
    )
    act = Act.objects.create(
        edition=edition, identifier=f"id-{n}",
        title="t", raw_text="r", search_text="s",
    )
    return Match.objects.create(watch=watch, act=act, category=category, state=state, rank=rank)


@pytest.fixture
def firm_a(db):
    return _member("Firm A", "a@firm.com")


@pytest.fixture
def firm_b(db):
    return _member("Firm B", "b@firm.com")


@pytest.mark.django_db
def test_feed_lists_only_own_workspace(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    _match(ws_a, date=datetime.date(2026, 7, 1))
    _match(ws_b, date=datetime.date(2026, 7, 1))
    api = APIClient()
    api.force_authenticate(user=user_a)
    resp = api.get("/api/matches")
    assert resp.status_code == 200
    assert resp.data["count"] == 1


@pytest.mark.django_db
def test_feed_filters_by_state(firm_a):
    ws, user = firm_a
    _match(ws, date=datetime.date(2026, 7, 1), state="new")
    _match(ws, date=datetime.date(2026, 7, 2), state="dismissed", rank=1.0)
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.get("/api/matches?state=new")
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["state"] == "new"


@pytest.mark.django_db
def test_feed_default_order_is_recency(firm_a):
    ws, user = firm_a
    old = _match(ws, date=datetime.date(2026, 7, 1))
    new = _match(ws, date=datetime.date(2026, 7, 2), rank=1.0)
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.get("/api/matches")
    assert resp.data["results"][0]["id"] == new.id  # newest created first


@pytest.mark.django_db
def test_mark_relevant_transitions_state(firm_a):
    ws, user = firm_a
    m = _match(ws, date=datetime.date(2026, 7, 1), state="new")
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(f"/api/matches/{m.id}/relevant")
    assert resp.status_code == 200
    m.refresh_from_db()
    assert m.state == "relevant"


@pytest.mark.django_db
def test_dismiss_transitions_state(firm_a):
    ws, user = firm_a
    m = _match(ws, date=datetime.date(2026, 7, 1), state="new")
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(f"/api/matches/{m.id}/dismiss")
    assert resp.status_code == 200
    m.refresh_from_db()
    assert m.state == "dismissed"


@pytest.mark.django_db
def test_cannot_triage_other_workspace_match(firm_a, firm_b):
    ws_a, user_a = firm_a
    ws_b, _ = firm_b
    m_b = _match(ws_b, date=datetime.date(2026, 7, 1), state="new")
    api = APIClient()
    api.force_authenticate(user=user_a)
    assert api.post(f"/api/matches/{m_b.id}/relevant").status_code == 404
    m_b.refresh_from_db()
    assert m_b.state == "new"
