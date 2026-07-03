import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import resolve_debug, resolve_secret_key, resolve_database_url


def test_resolve_debug_truthy_and_falsy():
    assert resolve_debug({"DJANGO_DEBUG": "1"}) is True
    assert resolve_debug({"DJANGO_DEBUG": "TRUE"}) is True
    assert resolve_debug({"DJANGO_DEBUG": "0"}) is False
    assert resolve_debug({}) is False


def test_resolve_secret_key_prefers_env():
    assert resolve_secret_key(debug=False, env={"SECRET_KEY": "real"}) == "real"


def test_resolve_secret_key_dev_fallback_only_in_debug():
    assert resolve_secret_key(debug=True, env={}) == "dev-insecure-key"


def test_resolve_secret_key_raises_in_prod_when_missing():
    with pytest.raises(ImproperlyConfigured):
        resolve_secret_key(debug=False, env={})


def test_resolve_database_url_precedence():
    assert resolve_database_url({"DATABASE_URL": "a", "SUPABASE_DB_URL": "b"}) == "a"
    assert resolve_database_url({"SUPABASE_DB_URL": "b"}) == "b"
    assert "localhost:5434" in resolve_database_url({})
