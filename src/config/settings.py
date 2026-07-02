import os

import dj_database_url

from config.env import resolve_database_url, resolve_debug, resolve_secret_key

DEBUG = resolve_debug()
SECRET_KEY = resolve_secret_key(debug=DEBUG)

# Enforced ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS are deferred to Plan 7 (no HTTP
# service is served in Plan 6 — this image only runs management commands).
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.postgres",
    "accounts",
    "watches",
    "gazette",
    "matching",
    "enrichment",
    "digests",
    "pipeline",
]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware"]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": dj_database_url.parse(resolve_database_url(), conn_max_age=0)}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

# HTTPS/security hardening — inert for the job, correct once a service is served (Plan 7).
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "config.json_log.JSONFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

REGWATCH_LLM_CLIENT = os.environ.get(
    "REGWATCH_LLM_CLIENT", "enrichment.anthropic_client.AnthropicLLMClient"
)
REGWATCH_EMAIL_SENDER = os.environ.get(
    "REGWATCH_EMAIL_SENDER", "digests.resend.ResendEmailSender"
)
REGWATCH_MAX_ENRICH_PER_RUN = int(os.environ.get("REGWATCH_MAX_ENRICH_PER_RUN", "200"))
