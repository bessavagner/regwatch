# src/gazette/inlabs/client.py
import datetime
import os

import httpx

DEFAULT_BASE_URL = "https://inlabs.in.gov.br"


class InlabsClient:
    def __init__(
        self,
        username: str,
        password: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        transport: httpx.BaseTransport | None = None,
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

    def login(self) -> None:
        self._http.post(
            "/logar.php",
            data={"email": self._username, "password": self._password},
        )
        if "inlabs_session_cookie" not in self._http.cookies:
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
        return self._http.get(
            "/index.php", params={"p": d, "dl": f"{d}-{section}.zip"}
        )

    def close(self) -> None:
        self._http.close()
