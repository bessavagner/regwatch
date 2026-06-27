# src/gazette/tests/test_inlabs_client.py
import datetime

import httpx
import pytest

from gazette.inlabs.client import InlabsClient

DATE = datetime.date(2026, 6, 26)
LOGIN_COOKIE = "inlabs_session_cookie=sess-abc; Path=/"


def _client(handler) -> InlabsClient:
    return InlabsClient(
        "user@example.com",
        "secret",
        base_url="https://inlabs.test",
        transport=httpx.MockTransport(handler),
    )


def test_login_sends_credentials_and_stores_cookie():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/logar.php"
        seen["body"] = request.content.decode()
        return httpx.Response(200, headers={"set-cookie": LOGIN_COOKIE})

    client = _client(handler)
    client.login()
    assert "email=user%40example.com" in seen["body"]
    assert "password=secret" in seen["body"]


def test_login_raises_when_cookie_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)  # no Set-Cookie

    with pytest.raises(RuntimeError):
        _client(handler).login()


def test_download_section_returns_zip_bytes():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/logar.php":
            return httpx.Response(200, headers={"set-cookie": LOGIN_COOKIE})
        assert request.url.params["dl"] == "2026-06-26-DO1.zip"
        return httpx.Response(200, content=b"PK\x03\x04zip-bytes")

    client = _client(handler)
    client.login()
    assert client.download_section(DATE, "DO1") == b"PK\x03\x04zip-bytes"


def test_download_section_absent_returns_none():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/logar.php":
            return httpx.Response(200, headers={"set-cookie": LOGIN_COOKIE})
        return httpx.Response(404, text="Not Found")

    client = _client(handler)
    client.login()
    assert client.download_section(DATE, "DO3E") is None


def test_download_section_non_pk_body_returns_none():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/logar.php":
            return httpx.Response(200, headers={"set-cookie": LOGIN_COOKIE})
        return httpx.Response(200, content=b"<html>login required</html>")

    client = _client(handler)
    client.login()
    assert client.download_section(DATE, "DO1") is None


def test_download_section_relogs_in_once_on_403():
    calls = {"login": 0, "download": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/logar.php":
            calls["login"] += 1
            return httpx.Response(200, headers={"set-cookie": LOGIN_COOKIE})
        calls["download"] += 1
        if calls["download"] == 1:
            return httpx.Response(403, text="session expired")
        return httpx.Response(200, content=b"PK\x03\x04ok")

    client = _client(handler)
    client.login()
    assert client.download_section(DATE, "DO1") == b"PK\x03\x04ok"
    assert calls["login"] == 2          # initial + one re-login
    assert calls["download"] == 2       # failed + retried


def test_section_url_is_absolute():
    url = _client(lambda r: httpx.Response(200)).section_url(DATE, "DO2")
    assert url == (
        "https://inlabs.test/index.php?p=2026-06-26&dl=2026-06-26-DO2.zip"
    )


def test_from_env_reads_credentials(monkeypatch):
    monkeypatch.setenv("INLABS_USERNAME", "env-user")
    monkeypatch.setenv("INLABS_PASSWORD", "env-pass")
    client = InlabsClient.from_env(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    assert client._username == "env-user"
    assert client._password == "env-pass"


def test_from_env_raises_when_missing(monkeypatch):
    monkeypatch.delenv("INLABS_USERNAME", raising=False)
    monkeypatch.delenv("INLABS_PASSWORD", raising=False)
    with pytest.raises(RuntimeError):
        InlabsClient.from_env()
