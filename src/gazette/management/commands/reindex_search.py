from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand
from django.db.models import F

from gazette.models import Act
from gazette.normalize import NormalizeNFC


class Command(BaseCommand):
    help = "Backfill Act.search_vector_pt in batches."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=500)
        parser.add_argument(
            "--all", action="store_true",
            help="Reindex every act, not just those with a null vector.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        qs = Act.objects.all() if options["all"] else Act.objects.filter(search_vector_pt=None)
        ids = list(qs.values_list("pk", flat=True))
        total = len(ids)
        done = 0
        # Batched on purpose: a single UPDATE over 22k acts holds one long
        # transaction against the production database.
        for start in range(0, total, batch_size):
            chunk = ids[start:start + batch_size]
            Act.objects.filter(pk__in=chunk).update(
                search_vector_pt=SearchVector(
                    NormalizeNFC(F("title")), NormalizeNFC(F("raw_text")), config="portuguese"
                )
            )
            done += len(chunk)
            self.stdout.write(f"reindexed {done}/{total}")
        self.stdout.write(f"reindex_search: {done} acts")
