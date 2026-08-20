import datetime

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from gazette.models import Act, Edition

BATCH = 2000

# Nulling the columns hands the space back to Postgres, not to the disk Supabase
# meters. Only a table rewrite plus a GIN rebuild returns it.
RECLAIM_SQL = (
    "VACUUM (FULL, ANALYZE) gazette_act",
    "REINDEX INDEX gazette_act_search_pt_gin",
    "REINDEX INDEX gazette_act_search_text_trgm",
)


class Command(BaseCommand):
    help = (
        "Drop act bodies older than the matching window: delete acts nothing "
        "ever matched, strip raw_text/search_text/search_vector_pt from the "
        "ones that did. Dry-run unless --apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="days of text to keep")
        parser.add_argument("--apply", action="store_true", help="actually prune")
        parser.add_argument(
            "--reclaim",
            action="store_true",
            help="VACUUM FULL + REINDEX afterwards; takes an exclusive lock on gazette_act",
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            self.stderr.write("--days must be at least 1")
            return
        apply = options["apply"]
        cutoff = timezone.localdate() - datetime.timedelta(days=days)

        # Matched acts are kept whatever their age: Match.act cascades, so
        # deleting one would silently delete a client's triaged history.
        stale = Act.objects.filter(edition__date__lt=cutoff)
        doomed = stale.filter(matches__isnull=True)
        strip = stale.filter(matches__isnull=False).exclude(raw_text="", search_text="")

        n_doomed = doomed.count()
        n_strip = strip.distinct().count()
        freed = self._payload_bytes(cutoff)

        self.stdout.write(
            f"cutoff {cutoff} (keeping {days} day(s) of text)\n"
            f"  delete (never matched): {n_doomed} act(s)\n"
            f"  strip  (has matches)  : {n_strip} act(s)\n"
            f"  text payload affected : {freed}"
        )

        if not apply:
            self.stdout.write("prune_act_text: dry run, nothing written")
            return

        deleted = 0
        while True:
            ids = list(doomed.values_list("id", flat=True)[:BATCH])
            if not ids:
                break
            Act.objects.filter(id__in=ids).delete()
            deleted += len(ids)
            self.stdout.write(f"  deleted {deleted}/{n_doomed}")

        stripped = strip.update(raw_text="", search_text="", search_vector_pt=None)

        # Mark every edition past the cutoff, not just the ones that lost text:
        # an edition whose acts were all deleted is just as unusable to backfill.
        editions = Edition.objects.filter(
            date__lt=cutoff, text_pruned_at__isnull=True
        ).update(text_pruned_at=timezone.now())

        self.stdout.write(
            f"prune_act_text: deleted {deleted}, stripped {stripped}, "
            f"marked {editions} edition(s) pruned"
        )

        if options["reclaim"]:
            self._reclaim()

    def _payload_bytes(self, cutoff) -> str:
        with connection.cursor() as cur:
            cur.execute(
                """
                select pg_size_pretty(coalesce(sum(
                    pg_column_size(a.raw_text)
                    + pg_column_size(a.search_text)
                    + pg_column_size(a.search_vector_pt)
                ), 0))
                from gazette_act a
                join gazette_edition e on e.id = a.edition_id
                where e.date < %s
                """,
                [cutoff],
            )
            return cur.fetchone()[0]

    def _reclaim(self):
        # VACUUM FULL cannot run inside a transaction block.
        with connection.cursor() as cur:
            for sql in RECLAIM_SQL:
                self.stdout.write(f"  {sql} ...")
                cur.execute(sql)
        self.stdout.write("prune_act_text: reclaim done")
