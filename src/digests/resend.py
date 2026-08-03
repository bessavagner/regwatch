import os

import httpx

RESEND_URL = "https://api.resend.com/emails"


class ResendEmailSender:
    def __init__(
        self,
        api_key: str,
        from_email: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ):
        self._api_key = api_key
        self._from = from_email
        self._http = httpx.Client(transport=transport, timeout=30.0)

    @classmethod
    def from_env(cls) -> "ResendEmailSender":
        try:
            api_key = os.environ["RESEND_API_KEY"]
            from_email = os.environ["RESEND_FROM"]
        except KeyError as exc:
            raise RuntimeError("RESEND_API_KEY and RESEND_FROM must be set") from exc
        return cls(api_key, from_email)

    def send(self, to: str, subject: str, body: str) -> None:
        resp = self._http.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"from": self._from, "to": to, "subject": subject, "text": body},
        )
        if resp.is_error:
            # Resend explains the refusal in the body ("domain not verified",
            # "you can only send testing emails to your own address");
            # raise_for_status alone reports just the status and hides it.
            # The body echoes no credentials, only the request's own fields.
            raise httpx.HTTPStatusError(
                f"Resend refused the send: {resp.status_code} "
                f"{resp.text[:300]} (from={self._from})",
                request=resp.request,
                response=resp,
            )
