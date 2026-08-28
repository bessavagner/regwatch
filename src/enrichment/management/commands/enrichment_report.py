import datetime
import json

from django.core.management.base import BaseCommand
from django.utils import timezone

from enrichment.report import (
    cluster_summaries,
    histogram,
    inconsistency_rate,
    modal_share,
)
from matching.models import Match

DEFAULT_DAYS = 7


def _parse(value: str | None) -> datetime.date | None:
    return datetime.date.fromisoformat(value) if value else None


class Command(BaseCommand):
    help = (
        "Measure enrichment quality over a date range: how often identical act "
        "types get different categories (D3), and how much spread the ranking "
        "signal has (D5). Read-only -- it sends nothing to any provider."
    )

    def add_arguments(self, parser):
        parser.add_argument("--date-from", help="YYYY-MM-DD (default: 7 days before --date-to)")
        parser.add_argument("--date-to", help="YYYY-MM-DD (default: today)")
        parser.add_argument("--client", type=int, help="restrict to one client id")
        parser.add_argument("--min-cluster", type=int, default=3)
        parser.add_argument("--json", action="store_true", help="machine-readable output")

    def handle(self, *args, **options):
        date_to = _parse(options["date_to"]) or timezone.localdate()
        date_from = _parse(options["date_from"]) or date_to - datetime.timedelta(days=DEFAULT_DAYS)

        qs = (
            Match.objects.filter(
                act__edition__date__gte=date_from, act__edition__date__lte=date_to
            )
            .exclude(ai_summary__isnull=True)
            .exclude(ai_summary="")
        )
        if options["client"]:
            qs = qs.filter(watch__client_id=options["client"])
        rows = list(qs.values_list("ai_summary", "category", "confidence"))

        clusters = cluster_summaries(
            [(summary, category) for summary, category, _ in rows],
            min_size=options["min_cluster"],
        )
        # Two decimal places: the values sit between 0.98 and 0.99, and rounding
        # any coarser would hide exactly the absence of spread being measured.
        conf = histogram([round(c, 2) for _, _, c in rows if c is not None])

        payload = {
            "date_from": str(date_from),
            "date_to": str(date_to),
            "min_cluster": options["min_cluster"],
            "enriched_matches": len(rows),
            "categories": histogram([category for _, category, _ in rows]),
            "clusters_measured": len(clusters),
            "inconsistency_rate": round(inconsistency_rate(clusters), 4),
            "split_clusters": [
                {"key": c.key, "size": c.size, "categories": dict(c.categories)}
                for c in clusters
                if not c.single_valued
            ],
            "confidence_histogram": {str(k): v for k, v in sorted(conf.items())},
            "confidence_modal_share": round(modal_share(conf), 4),
        }

        if options["json"]:
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        self._render(payload)

    def _render(self, p):
        self.stdout.write(
            f"{p['date_from']} -> {p['date_to']} — {p['enriched_matches']} enriched match(es)"
        )
        self.stdout.write("\ncategories:")
        for value, count in sorted(p["categories"].items(), key=lambda kv: -kv[1]):
            self.stdout.write(f"  {value or '(none)':<12} {count}")

        self.stdout.write(
            f"\nD3 — {p['clusters_measured']} cluster(s) of >= {p['min_cluster']} act(s); "
            f"inconsistency rate {p['inconsistency_rate']:.2%}"
        )
        for c in p["split_clusters"]:
            self.stdout.write(f"  {c['key']!r} ({c['size']}) -> {c['categories']}")

        self.stdout.write(
            f"\nD5 — confidence modal share {p['confidence_modal_share']:.2%} "
            f"across {len(p['confidence_histogram'])} distinct value(s)"
        )
        for value, count in p["confidence_histogram"].items():
            self.stdout.write(f"  {value:<6} {count}")
