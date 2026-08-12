from django.core.management.base import BaseCommand

from gazette.models import Act
from matching.matcher import _watch_q
from matching.models import Match
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
            # Only untriaged matches: a relevant/dismissed verdict is a human
            # decision, and rewriting history under it would be worse than a
            # stale row.
            stale_ids = list(
                Match.objects.filter(watch=watch, state="new").values_list("id", "act_id")
            )
            if not stale_ids:
                continue

            query = _watch_q(watch)
            if query is None:
                # The watch can never match anything; every match it holds is stale.
                keep: set[int] = set()
            else:
                keep = set(
                    Act.objects.filter(query, id__in=[a for _, a in stale_ids])
                    .values_list("id", flat=True)
                )

            doomed = [m for m, a in stale_ids if a not in keep]
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
