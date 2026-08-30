import datetime
import logging

from django.template.loader import render_to_string
from django.utils import timezone

from config.formatting import br_date
from gazette.models import Edition
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
        # Localised so the subject matches the body, instead of pairing a
        # Brazilian date with an ISO one in the same message.
        subject = f"RegWatch — {br_date(digest.date)}"
        sender.send(to=email, subject=subject, body=digest.body)
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


def clients_expecting_delivery(
    date: datetime.date, client: Client | None = None
):
    """Clients that should hear from us on `date` even with nothing to report.

    Gated on a published edition (decision-007): on a weekend or a national
    holiday there are no editions, nothing ran, and "your watches found
    nothing" would be noise that teaches the reader to ignore the message.

    Two further exclusions, both load-bearing:

    - a client with no *active* watch, because nothing ran for them either;
    - a client with no email address, because a quiet digest we can never
      deliver would sit sent=False forever and fail check_heartbeat every day,
      destroying the dead-man's switch this behaviour exists to feed.
    """
    if not Edition.objects.filter(date=date).exists():
        return Client.objects.none()
    qs = (
        Client.objects.filter(watches__active=True)
        .exclude(email="")
        .distinct()
        .order_by("pk")
    )
    if client is not None:
        qs = qs.filter(pk=client.pk)
    return qs


def build_and_send_digests(
    date: datetime.date, sender: EmailSender, client: Client | None = None
) -> list[Digest]:
    out: list[Digest] = []
    matches = (
        Match.objects.filter(act__edition__date=date)
        .select_related("watch__client", "act__edition")
        # Most signals first, then rank. rank is advisory and measures how
        # strongly the text matched, which is not the same question as whether
        # the act is worth reading; signal_score is what the client can check.
        # Section then id keep the order stable for equal scores instead of
        # letting it drift between runs of the same date.
        .order_by("-signal_score", "-rank", "act__edition__section", "id")
    )
    if client is not None:
        matches = matches.filter(watch__client=client)
    by_client: dict[int, list[Match]] = {}
    clients: dict[int, Client] = {}
    for m in matches:
        c = m.watch.client
        clients[c.pk] = c
        by_client.setdefault(c.pk, []).append(m)

    # Iterating clients rather than matches is the whole change: a client with
    # nothing to report never used to enter this loop, so silence meant both
    # "nothing concerned you" and "RegWatch is broken" (decision-007).
    for c in clients_expecting_delivery(date, client=client):
        clients.setdefault(c.pk, c)

    for client_id, c in clients.items():
        client_matches = by_client.get(client_id, [])
        template = "digests/daily.txt" if client_matches else "digests/quiet.txt"
        body = render_to_string(
            template,
            {"client": c, "date": br_date(date), "matches": client_matches},
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


def retry_unsent_digests(
    date_from: datetime.date,
    date_to: datetime.date,
    sender: EmailSender,
    client: Client | None = None,
) -> tuple[int, int]:
    """Re-attempt every unsent digest in [date_from, date_to].

    A digest whose send failed is otherwise unreachable: build_and_send_digests
    only ever revisits the date it is called with, and no later scheduled run
    processes a past date. Returns (sent, attempted).
    """
    qs = (
        Digest.objects.filter(sent=False, date__gte=date_from, date__lte=date_to)
        .select_related("client")
        .order_by("date", "client_id")
    )
    if client is not None:
        qs = qs.filter(client=client)

    attempted = sent = 0
    for digest in qs:
        attempted += 1
        if deliver_digest(digest, sender):
            sent += 1
    return sent, attempted
