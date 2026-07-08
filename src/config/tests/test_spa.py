import pytest
from django.test import Client


@pytest.mark.django_db
def test_root_serves_the_spa_shell():
    resp = Client().get("/")
    assert resp.status_code == 200
    assert b"<div id=\"app\">" in resp.content or b"RegWatch" in resp.content


@pytest.mark.django_db
def test_client_side_route_falls_through_to_spa():
    # A deep client route the SPA owns must return the shell, not 404.
    resp = Client().get("/watches")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_api_paths_are_not_swallowed_by_the_spa_catch_all():
    # /api still routes to DRF: unauthenticated /api/me is 401/403, never the SPA 200.
    resp = Client().get("/api/me")
    assert resp.status_code in (401, 403)
