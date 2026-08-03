import smtplib
import ssl

import pytest

from digests.smtp import SmtpEmailSender


class _FakeSMTP:
    """Stands in for smtplib.SMTP so the suite opens no socket."""

    def __init__(self, host, port, timeout=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.tls_context = None
        self.credentials = None
        self.messages = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True
        return False

    def starttls(self, context=None):
        self.tls_context = context

    def login(self, user, password):
        self.credentials = (user, password)

    def send_message(self, msg):
        self.messages.append(msg)


class _RecordingFactory:
    def __init__(self):
        self.instances = []

    def __call__(self, host, port, timeout=None):
        smtp = _FakeSMTP(host, port, timeout=timeout)
        self.instances.append(smtp)
        return smtp


def _sender(factory, **kwargs):
    defaults = {
        "host": "smtp.gmail.test", "port": 587, "user": "ops@gmail.test",
        "password": "app-password", "from_email": "RegWatch <ops@gmail.test>",
        "smtp_factory": factory,
    }
    return SmtpEmailSender(**{**defaults, **kwargs})


def test_send_delivers_over_starttls_then_logs_in():
    factory = _RecordingFactory()
    _sender(factory).send(to="firm@example.test", subject="s", body="b")

    smtp = factory.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.gmail.test", 587)
    # A verified context: create_default_context() checks the cert chain AND the
    # hostname; smtplib's bare starttls() does neither and would hand the app
    # password to any MITM peer.
    assert isinstance(smtp.tls_context, ssl.SSLContext)
    assert smtp.tls_context.verify_mode == ssl.CERT_REQUIRED
    assert smtp.tls_context.check_hostname is True
    assert smtp.credentials == ("ops@gmail.test", "app-password")
    assert len(smtp.messages) == 1
    assert smtp.closed is True


def test_send_builds_the_message_envelope():
    factory = _RecordingFactory()
    _sender(factory).send(
        to="firm@example.test",
        subject="RegWatch — 2026-08-03",
        body="Licença à BETA CORP.\n",
    )

    msg = factory.instances[0].messages[0]
    assert msg["From"] == "RegWatch <ops@gmail.test>"
    assert msg["To"] == "firm@example.test"
    assert msg["Subject"] == "RegWatch — 2026-08-03"
    assert "Licença à BETA CORP." in msg.get_content()


def test_refuses_to_send_the_password_over_an_unencrypted_channel():
    factory = _RecordingFactory()
    sender = _sender(factory, starttls=False)

    with pytest.raises(ValueError, match="STARTTLS"):
        sender.send(to="firm@example.test", subject="s", body="b")

    assert factory.instances == []  # fails before opening any connection


def test_sends_without_login_when_the_relay_needs_no_credential():
    factory = _RecordingFactory()
    _sender(factory, user="", password="", starttls=False).send(
        to="firm@example.test", subject="s", body="b"
    )

    smtp = factory.instances[0]
    assert smtp.credentials is None
    assert smtp.tls_context is None
    assert len(smtp.messages) == 1


def test_a_crlf_in_the_recipient_cannot_smuggle_a_header():
    """Client emails come from the database, so the recipient is not trusted."""
    factory = _RecordingFactory()
    sender = _sender(factory)

    with pytest.raises(ValueError):
        sender.send(to="firm@example.test\nBcc: attacker@evil.test", subject="s", body="b")

    assert factory.instances == []


def test_from_env_reads_config(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "ops@gmail.test")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password")
    monkeypatch.setenv("SMTP_FROM", "RegWatch <ops@gmail.test>")

    sender = SmtpEmailSender.from_env()

    assert sender._host == "smtp.gmail.com"
    assert sender._port == 465
    assert sender._user == "ops@gmail.test"
    assert sender._from == "RegWatch <ops@gmail.test>"
    assert sender._starttls is True
    assert sender._smtp is smtplib.SMTP


def test_from_env_defaults_the_port_to_587(monkeypatch):
    monkeypatch.delenv("SMTP_PORT", raising=False)
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_FROM", "RegWatch <ops@gmail.test>")

    assert SmtpEmailSender.from_env()._port == 587


@pytest.mark.parametrize("missing", ["SMTP_HOST", "SMTP_FROM"])
def test_from_env_raises_when_required_config_is_missing(monkeypatch, missing):
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_FROM", "RegWatch <ops@gmail.test>")
    monkeypatch.delenv(missing)

    with pytest.raises(RuntimeError, match="SMTP_HOST and SMTP_FROM"):
        SmtpEmailSender.from_env()


def test_its_send_signature_matches_the_email_sender_protocol():
    """notifier.py calls send(to=..., subject=..., body=...) by keyword, so a
    renamed parameter breaks delivery at runtime while still type-checking as
    'has a send method'."""
    import inspect

    from digests.email import EmailSender

    expected = inspect.signature(EmailSender.send)
    actual = inspect.signature(SmtpEmailSender.send)

    assert list(actual.parameters) == list(expected.parameters)
