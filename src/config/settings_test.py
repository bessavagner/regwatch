"""Test settings: force dev mode before importing the base settings.

Importing this module sets DJANGO_DEBUG before config.settings runs, so the
secure-by-default SECRET_KEY guard falls back to the dev key under pytest.
This relies only on ordinary Python import ordering, so a plain
`uv run pytest` works — unlike a conftest hook, which pytest-django outruns.
"""
import os

os.environ.setdefault("DJANGO_DEBUG", "1")

from config.settings import *  # noqa: E402,F401,F403
