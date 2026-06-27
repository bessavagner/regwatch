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


def test_fetch_editions_closes_self_constructed_client_even_on_error(monkeypatch):
    """Verify that fetch_editions closes a client it creates, even when download fails."""

    class FakeClient:
        def __init__(self):
            self.closed = False

        def login(self):
            pass

        def section_url(self, date, section):
            return f"https://fake.test/{date}/{section}"

        def download_section(self, date, section):
            raise RuntimeError("boom")

        def close(self):
            self.closed = True

    fake = FakeClient()
    monkeypatch.setattr(
        "gazette.inlabs.fetch.InlabsClient.from_env",
        classmethod(lambda cls, **kw: fake),
    )

    # Should raise RuntimeError from download_section
    try:
        fetch_editions(DATE)
        assert False, "Expected RuntimeError to be raised"
    except RuntimeError as e:
        assert str(e) == "boom"

    # But close() should still have been called due to try/finally
    assert fake.closed is True


def test_fetch_editions_does_not_close_injected_client(monkeypatch):
    """Verify that fetch_editions does NOT close an injected client."""

    close_call_count = [0]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/logar.php":
            return httpx.Response(200, headers={"set-cookie": LOGIN_COOKIE})
        return httpx.Response(404, text="Not Found")

    client = InlabsClient(
        "u", "p", base_url="https://inlabs.test",
        transport=httpx.MockTransport(handler),
    )

    # Spy on close() to track calls
    original_close = client.close
    def tracked_close():
        close_call_count[0] += 1
        original_close()

    monkeypatch.setattr(client, "close", tracked_close)

    # Call fetch_editions with injected client (all-404 handler returns [])
    result = fetch_editions(DATE, client=client)
    assert result == []

    # close() should never have been called
    assert close_call_count[0] == 0
