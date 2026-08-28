from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand
from django.db.models import F

from gazette.models import Act
from gazette.normalize import NormalizeNFC, normalize_text


class Command(BaseCommand):
    help = "Backfill Act.search_text and Act.search_vector_pt in batches."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=500)
        parser.add_argument(
            "--all", action="store_true",
            help="Reindex every act, not just those with a null vector.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        # Pruned acts are excluded whatever --all says: prune_act_text empties
        # raw_text/search_text and nulls the vector, and the null vector would
        # otherwise put every pruned row in the default selection. Rebuilding
        # them from the surviving title+agency re-inflates the GIN indexes the
        # prune exists to shrink.
        qs = Act.objects.exclude(raw_text="")
        if not options["all"]:
            qs = qs.filter(search_vector_pt=None)
        ids = list(qs.values_list("pk", flat=True))
        total = len(ids)
        done = 0
        # Batched on purpose: a single UPDATE over 22k acts holds one long
        # transaction against the production database.
        for start in range(0, total, batch_size):
            chunk = ids[start:start + batch_size]
            # search_text is recomputed in Python, not SQL: normalize_text
            # NFKD-decomposes and drops combining marks, which Postgres cannot
            # do without the unaccent extension this database does not install.
            acts = list(Act.objects.filter(pk__in=chunk))
            for act in acts:
                act.search_text = normalize_text(
                    f"{act.title} {act.agency} {act.raw_text}"
                )
            Act.objects.bulk_update(acts, ["search_text"], batch_size=batch_size)
            Act.objects.filter(pk__in=chunk).update(
                search_vector_pt=SearchVector(
                    NormalizeNFC(F("title")),
                    NormalizeNFC(F("agency")),
                    NormalizeNFC(F("raw_text")),
                    config="portuguese",
                )
            )
            done += len(chunk)
            self.stdout.write(f"reindexed {done}/{total}")
        self.stdout.write(f"reindex_search: {done} acts")
