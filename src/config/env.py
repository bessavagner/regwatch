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


def resolve_allowed_hosts(*, debug: bool, env=os.environ) -> list[str]:
    raw = env.get("DJANGO_ALLOWED_HOSTS", "").strip()
    if raw:
        return [h.strip() for h in raw.split(",") if h.strip()]
    if debug:
        return ["*"]
    # Non-serving processes (batch Jobs: migrate/run_daily/check_heartbeat) load
    # settings but serve no HTTP, so an unset host is harmless for them: return
    # Django's own default of []. The HTTP entrypoint enforces a real value via
    # require_allowed_hosts() so a misconfigured Service still fails fast.
    return []


def require_allowed_hosts(*, debug: bool, env=os.environ) -> list[str]:
    """Fail fast when the HTTP service has no ALLOWED_HOSTS in production.

    Called from config/wsgi.py (loaded only by gunicorn), so the batch Jobs are
    unaffected while a Service deployed without DJANGO_ALLOWED_HOSTS raises at
    boot instead of silently rejecting every request with 400 DisallowedHost.
    """
    hosts = resolve_allowed_hosts(debug=debug, env=env)
    if not debug and not hosts:
        raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must be set when DEBUG is False")
    return hosts


def resolve_csrf_trusted_origins(env=os.environ) -> list[str]:
    raw = env.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").strip()
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]
