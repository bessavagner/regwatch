"""Plain-SMTP digest transport, selected via REGWATCH_EMAIL_SENDER.

Chosen over a transactional-email API because RegWatch has no domain of its own
yet: an API like Resend refuses to send at all until a domain is verified, while
an authenticated SMTP relay (Gmail with an app password) delivers today, signed
by the relay's own DKIM.

The trade-off is real and worth stating: SMTP answers `250 OK` and tells you
nothing afterwards. There are no bounce or complaint callbacks, so a full
mailbox or a spam-marking is invisible here in a way it would not be behind an
API. Deliverability rests entirely on the relay's reputation, not RegWatch's.
See docs/runbook.md § "Send digests through Gmail SMTP".
"""

import os
import smtplib
import ssl
from email.message import EmailMessage


class SmtpEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        user: str,
        password: str,
        from_email: str,
        starttls: bool = True,
        timeout: float = 30.0,
        smtp_factory=smtplib.SMTP,
        ssl_context: ssl.SSLContext | None = None,
    ):
        self._host, self._port = host, port
        self._user, self._password = user, password
        self._from = from_email
        self._starttls = starttls
        self._timeout = timeout
        # The seam the suite tests through: no socket is opened in a test run.
        self._smtp = smtp_factory
        # create_default_context() verifies the certificate chain AND the hostname.
        # smtplib's bare starttls() does neither, and would hand AUTH LOGIN — and
        # the app password with it — to any peer that answers.
        self._ssl_context = ssl_context or ssl.create_default_context()

    @classmethod
    def from_env(cls) -> "SmtpEmailSender":
        try:
            host = os.environ["SMTP_HOST"]
            from_email = os.environ["SMTP_FROM"]
        except KeyError as exc:
            raise RuntimeError("SMTP_HOST and SMTP_FROM must be set") from exc
        return cls(
            host=host,
            port=int(os.environ.get("SMTP_PORT", "587")),
            user=os.environ.get("SMTP_USER", ""),
            password=os.environ.get("SMTP_PASSWORD", ""),
            from_email=from_email,
            starttls=os.environ.get("SMTP_STARTTLS", "true").strip().lower()
            not in {"false", "0", "no"},
        )

    def send(self, to: str, subject: str, body: str) -> None:
        if not self._starttls and self._user:
            raise ValueError(
                "SMTP_USER is set but SMTP_STARTTLS is off: refusing to send the "
                "SMTP password over an unencrypted channel. Enable STARTTLS, or "
                "use a relay that needs no credential."
            )
        # Built before connecting so a malformed recipient costs no connection.
        # Recipients come from the database, so they are not trusted input; the
        # default email policy rejects a CR/LF in a header outright, which makes
        # header injection structurally impossible rather than merely filtered.
        msg = EmailMessage()
        msg["From"] = self._from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        with self._smtp(self._host, self._port, timeout=self._timeout) as smtp:
            if self._starttls:
                smtp.starttls(context=self._ssl_context)
            if self._user:
                smtp.login(self._user, self._password)
            smtp.send_message(msg)
