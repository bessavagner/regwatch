import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Membership, Workspace
from enrichment.categories import CATEGORY_LABELS

User = get_user_model()


@pytest.fixture
def member(db):
    ws = Workspace.objects.create(name="Firm")
    user = User.objects.create_user(
        username="a@firm.com", email="a@firm.com", password="pw12345"
    )
    Membership.objects.create(workspace=ws, user=user)
    return user


@pytest.mark.django_db
def test_vocabulary_serves_every_category_with_its_label(member):
    api = APIClient()
    api.force_authenticate(member)
    body = api.get("/api/vocabulary").json()
    assert body["categories"] == [
        {"value": value, "label": label} for value, label in CATEGORY_LABELS.items()
    ]


@pytest.mark.django_db
def test_vocabulary_preserves_the_declared_order(member):
    # The SPA renders the filter dropdown straight from this list, so the order
    # is part of the contract, not an implementation detail.
    api = APIClient()
    api.force_authenticate(member)
    values = [c["value"] for c in api.get("/api/vocabulary").json()["categories"]]
    assert values == list(CATEGORY_LABELS)


@pytest.mark.django_db
def test_vocabulary_requires_a_session(db):
    assert APIClient().get("/api/vocabulary").status_code == 403
