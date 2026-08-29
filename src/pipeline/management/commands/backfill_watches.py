import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q

from matching.models import Match
from matching.stale import stale_match_ids
from pipeline import adapters
from pipeline.backfill import backfill_watch
from watches.models import Client


class _NoEnrichment:
    """Stands in for the provider when --max-enrich is 0.

    backfill_watch takes an LLMClient but never touches it once the budget is
    spent, and 0 is spent from the start. Passing this instead of a real client
    means a coverage backtest needs no API credentials at all, and turns a
    budget bug into a loud failure rather than a silent bill.
    """

    def summarize(self, act_text, terms):
        raise AssertionError("enrichment attempted with --max-enrich 0")


def _parse(value: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise CommandError(f"{value!r} is not a YYYY-MM-DD date") from exc


class Command(BaseCommand):
    help = (
        "Re-run a client's watches over past publication dates and report which "
        "watch fired on what, so a new watch can be evaluated before it is left "
        "to run. Re-fetches from INlabs, because prune_act_text deletes acts no "
        "watch matched -- stored history is biased to what the old watches hit. "
        "Matches only by default: --max-enrich 0 sends nothing to the provider."
    )

    def add_arguments(self, parser):
        parser.add_argument("--client", type=int, required=True, help="client id")
        parser.add_argument("--date-from", required=True, help="YYYY-MM-DD")
        parser.add_argument("--date-to", required=True, help="YYYY-MM-DD")
        parser.add_argument(
            "--max-enrich", type=int, default=0,
            help="cap on acts sent to the provider; 0 (the default) means match only",
        )
        parser.add_argument(
            "--apply", action="store_true",
            help="actually fetch and match; without it nothing is written",
        )

    def handle(self, *args, **options):
        try:
            client = Client.objects.get(pk=options["client"])
        except Client.DoesNotExist as exc:
            raise CommandError(f"no client with id {options['client']}") from exc

        date_from = _parse(options["date_from"])
        date_to = _parse(options["date_to"])
        if date_from > date_to:
            raise CommandError("--date-from is after --date-to")

        days = (date_to - date_from).days + 1
        enrich = options["max_enrich"]
        if not options["apply"]:
            self.stdout.write(
                f"would back-fill {client.name} (client {client.pk}) over "
                f"{date_from} -> {date_to} ({days} day(s))\n"
                f"  provider    : {'no calls (match only)' if enrich == 0 else f'up to {enrich} act(s)'}\n"
                "  note        : each missing date is re-fetched from INlabs and "
                "ingested, which grows storage until prune_act_text runs\n"
                "dry run, nothing written -- re-run with --apply"
            )
            return

        # Editing a watch does not delete the rows its old terms produced, so a
        # per-watch count would mix two term sets and report the pre-edit answer
        # unchanged -- precisely when the number is being used to judge an edit.
        # Untriaged rows only; a human verdict outranks a term change.
        cleared = 0
        for watch in client.watches.all():
            doomed = stale_match_ids(watch, date_from=date_from, date_to=date_to)
            if doomed:
                Match.objects.filter(id__in=doomed).delete()
                cleared += len(doomed)
        if cleared:
            self.stdout.write(
                f"cleared {cleared} stale match(es) the current terms no longer make"
            )

        llm = _NoEnrichment() if enrich == 0 else adapters.get_llm_client()
        result = backfill_watch(
            date_from, date_to, llm, client.pk, max_enrich=enrich
        )
        self.stdout.write(
            f"{client.name}: {result.editions} edition(s), {result.acts} act(s), "
            f"{result.matches} match(es), {result.enriched} enriched"
        )
        if result.skipped_dates:
            # A skipped date is usually a weekend or a holiday, but a fetch
            # failure lands here too -- name them so the two are told apart.
            self.stdout.write(f"skipped (no edition or fetch failed): {', '.join(result.skipped_dates)}")

        # The evaluation itself: a watch that matched nothing has to be visible
        # as a zero, or it looks exactly like a watch that was never run.
        rows = (
            client.watches.annotate(
                hits=Count("matches", filter=Q(
                    matches__act__edition__date__gte=date_from,
                    matches__act__edition__date__lte=date_to,
                ))
            )
            .order_by("-hits", "pk")
        )
        self.stdout.write(f"\nper watch, {date_from} -> {date_to}:")
        for watch in rows:
            terms = ", ".join(
                t["text"] for g in (watch.groups or []) for t in (g.get("terms") or [])
            )[:70]
            flag = "" if watch.active else "  (inactive)"
            self.stdout.write(
                f"  watch {watch.pk:<4} {watch.hits:>4} match(es)  "
                f"[{watch.section or 'all'}] {terms}{flag}"
            )
