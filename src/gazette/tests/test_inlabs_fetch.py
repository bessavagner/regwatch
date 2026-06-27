# src/gazette/tests/test_inlabs_fetch.py
import datetime
import io
import zipfile
from pathlib import Path

import httpx

from gazette.inlabs import fetch_editions
from gazette.inlabs.client import InlabsClient
from gazette.inlabs.fetch import content_hash

DATE = datetime.date(2026, 6, 26)
FIXTURES = Path(__file__).parent / "fixtures" / "dou"
LOGIN_COOKIE = "inlabs_session_cookie=sess-abc; Path=/"


def _zip_of(*names: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name in names:
            zf.writestr(name, (FIXTURES / name).read_bytes())
    return buf.getvalue()


def test_content_hash_is_stable_and_sensitive():
    assert content_hash(b"PKabc") == content_hash(b"PKabc")
    assert content_hash(b"PKabc") != content_hash(b"PKxyz")
    assert len(content_hash(b"PKabc")) == 64  # sha256 hex


def test_fetch_editions_downloads_present_sections_and_parses_them():
    do1 = _zip_of("do1_portaria_50000041.xml", "do1_retificacao_50004579.xml")
    do2 = _zip_of("do2_portaria_49992072.xml", "do2_despacho_49991862.xml")
    available = {"2026-06-26-DO1.zip": do1, "2026-06-26-DO2.zip": do2}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/logar.php":
            return httpx.Response(200, headers={"set-cookie": LOGIN_COOKIE})
        dl = request.url.params["dl"]
        if dl in available:
            return httpx.Response(200, content=available[dl])
        return httpx.Response(404, text="Not Found")  # other sections absent

    client = InlabsClient(
        "u", "p", base_url="https://inlabs.test",
        transport=httpx.MockTransport(handler),
    )
    editions = fetch_editions(DATE, client=client)

    assert [e.section for e in editions] == ["DO1", "DO2"]
    assert all(e.date == DATE for e in editions)
    assert editions[0].source_url == (
        "https://inlabs.test/index.php?p=2026-06-26&dl=2026-06-26-DO1.zip"
    )
    assert {i.identifier for i in editions[0].items} == {"50000041", "50004579"}
    assert {i.identifier for i in editions[1].items} == {"49992072", "49991862"}


def test_fetch_editions_returns_empty_when_nothing_published():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/logar.php":
            return httpx.Response(200, headers={"set-cookie": LOGIN_COOKIE})
        return httpx.Response(404, text="Not Found")

    client = InlabsClient(
        "u", "p", base_url="https://inlabs.test",
        transport=httpx.MockTransport(handler),
    )
    assert fetch_editions(DATE, client=client) == []
