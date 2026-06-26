import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key")
DEBUG = True
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
MIDDLEWARE = []
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get(
            "DATABASE_URL",
            "postgres://regwatch:regwatch@localhost:5434/regwatch",
        )
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
