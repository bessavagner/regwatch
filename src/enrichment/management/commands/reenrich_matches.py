import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from enrichment.enricher import enrich_match
from enrichment.fallback import FallbackLLMClient
from matching.models import Match

DEFAULT_DAYS = 7
DEFAULT_LIMIT = 100


def _parse(value: str | None) -> datetime.date | None:
    return datetime.date.fromisoformat(value) if value else None


class Command(BaseCommand):
    help = (
        "Re-run enrichment over matches whose act text is still retained, so a "
        "prompt change can be measured against the same acts. Overwrites the "
        "stored summary, category and signals. Dry-run unless --apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument("--date-from", help="YYYY-MM-DD (default: 7 days before --date-to)")
        parser.add_argument("--date-to", help="YYYY-MM-DD (default: today)")
        parser.add_argument("--client", type=int, help="restrict to one client id")
        parser.add_argument(
            "--limit", type=int, default=DEFAULT_LIMIT,
            help="hard cap on how many acts are sent to the provider",
        )
        parser.add_argument("--apply", action="store_true", help="actually send them")

    def handle(self, *args, **options):
        date_to = _parse(options["date_to"]) or timezone.localdate()
        date_from = _parse(options["date_from"]) or date_to - datetime.timedelta(days=DEFAULT_DAYS)

        qs = (
            Match.objects.filter(
                act__edition__date__gte=date_from, act__edition__date__lte=date_to
            )
            # prune_act_text empties raw_text past the retention window. An act
            # with no body cannot be re-enriched, only re-guessed.
            .exclude(act__raw_text="")
            .select_related("act", "watch")
            .order_by("id")
        )
        if options["client"]:
            qs = qs.filter(watch__client_id=options["client"])
        matches = list(qs[: max(0, options["limit"])])

        self.stdout.write(
            f"{date_from} -> {date_to}: {len(matches)} match(es) with retained text"
            + ("" if options["apply"] else " (dry run, nothing sent)")
        )
        if not options["apply"]:
            self.stdout.write("re-run with --apply to send them to the provider")
            return
        if not matches:
            return

        client = FallbackLLMClient.from_env()
        for i, match in enumerate(matches, 1):
            # enrich_match logs and swallows a provider failure, so this is a
            # count of what was sent, not of what came back usable. The report
            # command is what says whether it worked.
            enrich_match(match, client)
            if i % 25 == 0:
                self.stdout.write(f"  {i}/{len(matches)}")
        self.stdout.write(f"sent {len(matches)} match(es) to the provider")
