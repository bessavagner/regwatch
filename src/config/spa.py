from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse

_PLACEHOLDER = (
    b"<!doctype html><html><head><title>RegWatch</title></head>"
    b'<body><div id="app"></div>'
    b"<!-- SPA build not present; run `npm run build` in web/ --></body></html>"
)


def spa_index(request):
    index = Path(settings.SPA_DIST_DIR) / "index.html"
    if index.is_file():
        return FileResponse(index.open("rb"), content_type="text/html")
    return HttpResponse(_PLACEHOLDER, content_type="text/html")
