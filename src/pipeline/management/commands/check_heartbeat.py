import datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError

from digests.models import Digest
from pipeline.models import RunLog

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


class Command(BaseCommand):
    help = "Exit non-zero if no successful RunLog exists for the date (dead-man's switch)."

    def add_arguments(self, parser):
        parser.add_argument("--date", default=None, help="YYYY-MM-DD (default: today in BRT)")

    def handle(self, *args, **options):
        if options["date"]:
            date = datetime.date.fromisoformat(options["date"])
        else:
            date = datetime.datetime.now(SAO_PAULO).date()

        log = (
            RunLog.objects.filter(date=date, trigger="scheduled")
            .order_by("-started_at")
            .first()
        )
        if log is None or log.status not in ("success", "partial"):
            raise CommandError(f"heartbeat: no completed scheduled RunLog for {date}")

        # A dead-man's switch that only asks "did the process exit zero" cannot
        # see the failure that actually matters: on 2026-08-11 the run reported
        # success while every digest went undelivered.
        if log.status == "partial":
            raise CommandError(f"heartbeat: run for {date} was partial — {log.errors}")

        undelivered = Digest.objects.filter(date=date, sent=False).count()
        if undelivered:
            raise CommandError(
                f"heartbeat: {undelivered} undelivered digest(s) for {date}"
            )

        self.stdout.write(
            f"heartbeat OK: {date} matched {log.matches}, delivered {log.digests_sent}"
        )
