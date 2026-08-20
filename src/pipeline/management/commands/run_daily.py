import datetime
import traceback
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from gazette.inlabs import fetch_editions
from gazette.models import Act, Edition
from matching.models import Match
from digests.models import Digest
from pipeline.adapters import get_llm_client, get_email_sender
from pipeline.runner import run_pipeline
from pipeline.models import RunLog

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


class Command(BaseCommand):
    help = "Fetch the day's DOU, run the pipeline, and record a RunLog."

    def add_arguments(self, parser):
        parser.add_argument("--date", default=None, help="YYYY-MM-DD (default: today in BRT)")

    def handle(self, *args, **options):
        if options["date"]:
            run_date = datetime.date.fromisoformat(options["date"])
        else:
            run_date = datetime.datetime.now(SAO_PAULO).date()

        log = RunLog.objects.create(date=run_date, status="running")
        try:
            editions = fetch_editions(run_date)
            result = run_pipeline(
                editions,
                get_llm_client(),
                get_email_sender(),
                max_enrich=settings.REGWATCH_MAX_ENRICH_PER_RUN,
                today=run_date,
            )
            log.ingested_acts = result.ingested_acts
            log.created_matches = result.created_matches
            log.created_enriched = result.created_enriched

            ed_qs = Edition.objects.filter(date=run_date)
            log.editions = ed_qs.count()
            log.acts = Act.objects.filter(edition__in=ed_qs).count()
            run_matches = Match.objects.filter(act__edition__date=run_date)
            log.matches = run_matches.count()
            log.enriched = run_matches.exclude(ai_summary__isnull=True).count()
            day_digests = Digest.objects.filter(date=run_date)
            log.digests = day_digests.count()
            log.digests_sent = day_digests.filter(sent=True).count()

            # A run that scraped and matched but delivered nothing is not a
            # success. Saying so here is what makes check_heartbeat able to see
            # a silent failure at all.
            shortfalls = []
            if log.matches and log.enriched < log.matches:
                shortfalls.append(f"{log.matches - log.enriched} matches not enriched")
            if log.digests_sent < log.digests:
                shortfalls.append(f"{log.digests - log.digests_sent} digests not sent")
            log.status = "partial" if shortfalls else "success"
            log.errors = "; ".join(shortfalls)
        except Exception:
            log.status = "failed"
            log.errors = traceback.format_exc()
            log.finished_at = timezone.now()
            log.save()
            raise
        log.finished_at = timezone.now()
        log.save()
        # Both views, labelled: what this run did, then the day's totals. Only
        # the first tells you whether the run was worth anything.
        self.stdout.write(
            f"run_daily {run_date}: this run ingested={log.ingested_acts} "
            f"matched={log.created_matches} enriched={log.created_enriched} | "
            f"date totals editions={log.editions} acts={log.acts} "
            f"matches={log.matches} enriched={log.enriched} digests={log.digests} "
            f"digests_sent={log.digests_sent} status={log.status}"
        )
