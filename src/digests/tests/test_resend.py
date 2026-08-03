import httpx
import pytest

from digests.resend import ResendEmailSender


def test_send_posts_to_resend_with_auth_and_payload():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["json"] = __import__("json").loads(request.content)
        return httpx.Response(200, json={"id": "email_123"})

    sender = ResendEmailSender(
        "re_test_key", "RegWatch <alerts@regwatch.test>",
        transport=httpx.MockTransport(handler),
    )
    sender.send(to="firm@example.test", subject="RegWatch — 2026-06-26", body="digest body")

    assert seen["url"] == "https://api.resend.com/emails"
    assert seen["auth"] == "Bearer re_test_key"
    assert seen["json"]["from"] == "RegWatch <alerts@regwatch.test>"
    assert seen["json"]["to"] == "firm@example.test"
    assert seen["json"]["subject"] == "RegWatch — 2026-06-26"
    assert seen["json"]["text"] == "digest body"


def test_send_raises_on_error_status():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "invalid from"})

    sender = ResendEmailSender("k", "x@y.test", transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        sender.send(to="a@b.test", subject="s", body="b")


def test_from_env_reads_config(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_env")
    monkeypatch.setenv("RESEND_FROM", "RegWatch <a@b.test>")
    sender = ResendEmailSender.from_env()
    assert sender._api_key == "re_env"
    assert sender._from == "RegWatch <a@b.test>"


def test_from_env_raises_when_missing(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM", raising=False)
    with pytest.raises(RuntimeError):
        ResendEmailSender.from_env()


def test_send_error_reports_the_resend_response_body():
    """A bare raise_for_status hides *why* Resend refused, which cost days of
    guessing on the 403s that started 2026-07-23."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={
            "statusCode": 403,
            "name": "validation_error",
            "message": "You can only send testing emails to your own email address",
        })

    sender = ResendEmailSender(
        "re_super_secret", "onboarding@resend.dev",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(httpx.HTTPStatusError) as exc:
        sender.send(to="firm@example.test", subject="s", body="b")

    message = str(exc.value)
    assert "403" in message
    assert "only send testing emails" in message
    assert "re_super_secret" not in message  # never leak the key into logs
