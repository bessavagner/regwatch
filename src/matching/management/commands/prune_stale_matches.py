from django.core.management.base import BaseCommand

from matching.models import Match
from matching.stale import stale_match_ids
from watches.models import Watch


class Command(BaseCommand):
    help = (
        "Delete untriaged matches that their watch's current definition would "
        "no longer produce. Dry-run unless --apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="actually delete")
        parser.add_argument("--watch", type=int, default=None, help="limit to one watch id")

    def handle(self, *args, **options):
        watches = Watch.objects.all()
        if options["watch"]:
            watches = watches.filter(pk=options["watch"])

        total = 0
        for watch in watches.select_related("client"):
            doomed = stale_match_ids(watch)
            if not doomed:
                continue
            total += len(doomed)
            self.stdout.write(
                f"watch {watch.pk} ({watch.client.name}): {len(doomed)} stale"
            )
            if options["apply"]:
                Match.objects.filter(id__in=doomed).delete()

        verb = "deleted" if options["apply"] else "would delete"
        self.stdout.write(f"prune_stale_matches: {verb} {total} match(es)")
