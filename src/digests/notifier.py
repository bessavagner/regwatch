import datetime
from django.template.loader import render_to_string
from watches.models import Client
from matching.models import Match
from digests.email import EmailSender
from digests.models import Digest


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
        if not digest.sent and c.email:
            sender.send(to=c.email, subject=f"RegWatch — {date}", body=body)
            digest.sent = True
            digest.save(update_fields=["sent"])
        out.append(digest)
    return out
