# src/gazette/inlabs/client.py
import datetime
import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://inlabs.in.gov.br"
TRANSIENT_STATUS_CODES = {502, 503, 504}
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = 1.0


class InlabsClient:
    def __init__(
        self,
        username: str,
        password: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        sleep=time.sleep,
    ):
        self._username = username
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self._base_url,
            transport=transport,
            follow_redirects=True,
            timeout=60.0,
        )
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds
        self._sleep = sleep

    @classmethod
    def from_env(cls, **kwargs) -> "InlabsClient":
        try:
            username = os.environ["INLABS_USERNAME"]
            password = os.environ["INLABS_PASSWORD"]
        except KeyError as exc:
            raise RuntimeError(
                "INLABS_USERNAME and INLABS_PASSWORD must be set"
            ) from exc
        return cls(username, password, **kwargs)

    def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        # INlabs is intermittently flaky (connection drops, 502/503/504); a
        # single blip previously aborted the whole day's pipeline run. Only
        # transient failures are retried — 4xx and well-formed-but-wrong
        # responses (e.g. bad credentials) are real failures, not blips.
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._http.request(method, url, **kwargs)
            except httpx.TransportError:
                if attempt == self._max_attempts:
                    raise
                self._sleep(self._backoff_seconds * attempt)
                continue
            if response.status_code in TRANSIENT_STATUS_CODES and attempt < self._max_attempts:
                self._sleep(self._backoff_seconds * attempt)
                continue
            return response

    def login(self) -> None:
        response = self._request_with_retry(
            "POST",
            "/logar.php",
            data={"email": self._username, "password": self._password},
        )
        if "inlabs_session_cookie" not in self._http.cookies:
            # Never log credentials here — only response metadata, to distinguish an
            # upstream outage (e.g. a "Sistema em Manutenção" 502 page) from a rejected
            # login (redirected back to the login page) without needing manual repro.
            logger.error(
                "INlabs login failed: status=%s body_preview=%r",
                response.status_code,
                response.text[:300],
            )
            raise RuntimeError("INlabs login failed: session cookie not set")

    def section_url(self, date: datetime.date, section: str) -> str:
        d = date.isoformat()
        return f"{self._base_url}/index.php?p={d}&dl={d}-{section}.zip"

    def download_section(self, date: datetime.date, section: str) -> bytes | None:
        resp = self._get_zip(date, section)
        if resp.status_code in (401, 403):
            self.login()
            resp = self._get_zip(date, section)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        body = resp.content
        return body if body.startswith(b"PK") else None

    def _get_zip(self, date: datetime.date, section: str) -> httpx.Response:
        d = date.isoformat()
        return self._request_with_retry(
            "GET", "/index.php", params={"p": d, "dl": f"{d}-{section}.zip"}
        )

    def close(self) -> None:
        self._http.close()
