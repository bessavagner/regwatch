import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # ./src
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Fail fast if the HTTP service is deployed without ALLOWED_HOSTS in production.
# Only this WSGI entrypoint (loaded by gunicorn) enforces it; the batch Jobs,
# which serve no HTTP, boot with ALLOWED_HOSTS=[] unaffected.
from config.env import require_allowed_hosts, resolve_debug

require_allowed_hosts(debug=resolve_debug())

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
