import os

from django.core.exceptions import ImproperlyConfigured

DEV_SECRET_KEY = "dev-insecure-key"
LOCAL_DB_DEFAULT = "postgres://regwatch:regwatch@localhost:5434/regwatch"
_TRUTHY = {"1", "true", "yes", "on"}


def resolve_debug(env=os.environ) -> bool:
    return env.get("DJANGO_DEBUG", "").strip().lower() in _TRUTHY


def resolve_secret_key(*, debug: bool, env=os.environ) -> str:
    key = env.get("SECRET_KEY")
    if key:
        return key
    if debug:
        return DEV_SECRET_KEY
    raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is False")


def resolve_database_url(env=os.environ) -> str:
    return env.get("DATABASE_URL") or env.get("SUPABASE_DB_URL") or LOCAL_DB_DEFAULT
