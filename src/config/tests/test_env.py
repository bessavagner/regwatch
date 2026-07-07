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


def test_allowed_hosts_from_env_splits_and_strips():
    from config.env import resolve_allowed_hosts

    env = {"DJANGO_ALLOWED_HOSTS": "api.example.com, .run.app "}
    assert resolve_allowed_hosts(debug=False, env=env) == ["api.example.com", ".run.app"]


def test_allowed_hosts_defaults_to_wildcard_in_debug():
    from config.env import resolve_allowed_hosts

    assert resolve_allowed_hosts(debug=True, env={}) == ["*"]


def test_allowed_hosts_raises_when_unset_and_not_debug():
    from config.env import resolve_allowed_hosts

    with pytest.raises(ImproperlyConfigured):
        resolve_allowed_hosts(debug=False, env={})


def test_csrf_trusted_origins_from_env():
    from config.env import resolve_csrf_trusted_origins

    env = {"DJANGO_CSRF_TRUSTED_ORIGINS": "https://api.example.com, https://app.example.com"}
    assert resolve_csrf_trusted_origins(env=env) == [
        "https://api.example.com",
        "https://app.example.com",
    ]


def test_csrf_trusted_origins_empty_default():
    from config.env import resolve_csrf_trusted_origins

    assert resolve_csrf_trusted_origins(env={}) == []
