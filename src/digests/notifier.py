import datetime
from django.template.loader import render_to_string
from watches.models import Client
from matching.models import Match
from digests.email import EmailSender
from digests.models import Digest


def build_and_send_digests(date: datetime.date, sender: EmailSender) -> list[Digest]:
    out: list[Digest] = []
    matches = (
        Match.objects.filter(act__edition__date=date)
        .select_related("watch__client", "act")
    )
    by_client: dict[int, list[Match]] = {}
    clients: dict[int, Client] = {}
    for m in matches:
        client = m.watch.client
        clients[client.pk] = client
        by_client.setdefault(client.pk, []).append(m)

    for client_id, client_matches in by_client.items():
        client = clients[client_id]
        body = render_to_string(
            "digests/daily.txt",
            {"client": client, "date": date, "matches": client_matches},
        )
        digest, _ = Digest.objects.update_or_create(
            client=client, date=date, defaults={"body": body},
        )
        if not digest.sent:
            sender.send(to=f"{client.name}", subject=f"RegWatch — {date}", body=body)
            digest.sent = True
            digest.save(update_fields=["sent"])
        out.append(digest)
    return out
