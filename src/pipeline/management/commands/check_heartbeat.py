import datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError

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

        if not RunLog.objects.filter(date=date, status="success").exists():
            raise CommandError(f"heartbeat: no successful RunLog for {date}")
        self.stdout.write(f"heartbeat OK: successful RunLog for {date}")
