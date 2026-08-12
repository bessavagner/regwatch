import datetime
import logging

from django.template.loader import render_to_string
from django.utils import timezone
from watches.models import Client
from matching.models import Match
from digests.email import EmailSender
from digests.models import Digest

logger = logging.getLogger(__name__)


def deliver_digest(digest: Digest, sender: EmailSender) -> bool:
    """Send one digest, recording the outcome on the row. Never raises.

    Returns True only when the transport accepted the message. A failure is
    recorded rather than propagated so that one rejected recipient cannot cost
    every other client their digest, nor discard a run whose scrape and
    matching succeeded.
    """
    if digest.sent:
        return True

    email = digest.client.email
    digest.send_attempts += 1
    digest.last_attempt_at = timezone.now()

    if not email:
        digest.send_error = "no email address on the client"
        digest.save(update_fields=["send_error", "send_attempts", "last_attempt_at"])
        return False

    try:
        sender.send(to=email, subject=f"RegWatch — {digest.date}", body=digest.body)
    except Exception as exc:
        logger.exception(
            "digest send failed for client %s on %s — leaving it unsent",
            digest.client_id, digest.date,
        )
        digest.send_error = f"{type(exc).__name__}: {exc}"[:2000]
        digest.save(update_fields=["send_error", "send_attempts", "last_attempt_at"])
        return False

    digest.sent = True
    digest.send_error = ""
    digest.save(
        update_fields=["sent", "send_error", "send_attempts", "last_attempt_at"]
    )
    return True


def build_and_send_digests(
    date: datetime.date, sender: EmailSender, client: Client | None = None
) -> list[Digest]:
    out: list[Digest] = []
    matches = (
        Match.objects.filter(act__edition__date=date)
        .select_related("watch__client", "act")
    )
    if client is not None:
        matches = matches.filter(watch__client=client)
    by_client: dict[int, list[Match]] = {}
    clients: dict[int, Client] = {}
    for m in matches:
        c = m.watch.client
        clients[c.pk] = c
        by_client.setdefault(c.pk, []).append(m)

    for client_id, client_matches in by_client.items():
        c = clients[client_id]
        body = render_to_string(
            "digests/daily.txt",
            {"client": c, "date": date, "matches": client_matches},
        )
        digest, _ = Digest.objects.update_or_create(
            client=c, date=date, defaults={"body": body},
        )
        # The in-memory instance carries the client we already fetched, so
        # deliver_digest does not re-query for it.
        digest.client = c
        deliver_digest(digest, sender)
        out.append(digest)
    return out
