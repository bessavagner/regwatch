import datetime

from django.core.management.base import BaseCommand

from digests.notifier import retry_unsent_digests
from pipeline.adapters import get_email_sender
from watches.models import Client


class Command(BaseCommand):
    help = "Re-attempt delivery of digests left unsent by an earlier run."

    def add_arguments(self, parser):
        parser.add_argument("--date-from", required=True, help="YYYY-MM-DD")
        parser.add_argument("--date-to", required=True, help="YYYY-MM-DD")
        parser.add_argument("--client", type=int, default=None, help="Client id (optional)")

    def handle(self, *args, **options):
        date_from = datetime.date.fromisoformat(options["date_from"])
        date_to = datetime.date.fromisoformat(options["date_to"])
        client = Client.objects.get(pk=options["client"]) if options["client"] else None

        sent, attempted = retry_unsent_digests(
            date_from, date_to, get_email_sender(), client
        )
        self.stdout.write(
            f"resend_digests {date_from}..{date_to}: resent {sent} of {attempted}"
        )
