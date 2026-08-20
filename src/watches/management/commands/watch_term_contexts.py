import re
from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from gazette.normalize import normalize_text
from matching.models import Match
from watches.grouping import iter_terms
from watches.models import Watch


class Command(BaseCommand):
    help = (
        "Show the recurring phrases around each of a watch's terms in the acts "
        "it matched, so the noisy ones can be turned into excludes."
    )

    def add_arguments(self, parser):
        parser.add_argument("--watch", type=int, required=True, help="watch id")
        parser.add_argument("--top", type=int, default=10, help="phrases per term")
        parser.add_argument(
            "--window", type=int, default=3, help="words of context on each side"
        )

    def handle(self, *args, **options):
        try:
            watch = Watch.objects.select_related("client").get(pk=options["watch"])
        except Watch.DoesNotExist:
            raise CommandError(f"no watch with id {options['watch']}")

        rows = list(
            Match.objects.filter(watch=watch)
            .select_related("act")
            .values_list("act__search_text", flat=True)
        )
        texts = [t for t in rows if t]
        pruned = len(rows) - len(texts)

        self.stdout.write(
            f"watch {watch.pk} ({watch.client.name}) — {len(texts)} matched act(s) "
            f"with text" + (f", {pruned} pruned and skipped" if pruned else "")
        )
        if not texts:
            self.stdout.write(
                "nothing to report: every matched act is past the text retention "
                "window (see docs/runbook.md, \"Prune act text\")"
            )
            return

        for text, kind in iter_terms(watch.groups):
            self._report_term(text, kind, texts, options["top"], options["window"])

    def _report_term(self, term, kind, texts, top, window):
        needle = normalize_text(term)
        esc = re.escape(needle)
        # search_text is already lowercased and accent-stripped, so \w is
        # enough for word boundaries here. Left and right context are counted
        # SEPARATELY: a two-sided window fragments on the numbers and dates that
        # follow most DOU phrases, so the recurring half never aggregates.
        # Built by concatenation, not a format string: the regex's own {1,N}
        # quantifier braces would have to be escaped in either .format or an
        # f-string, which reads worse than this.
        reps = "{1," + str(window) + "}"
        left_re = re.compile(r"((?:\w+\W+)" + reps + r")" + esc)
        right_re = re.compile(esc + r"((?:\W+\w+)" + reps + r")")

        left, right = Counter(), Counter()
        hit_acts = 0
        for text in texts:
            hit = False
            for m in left_re.finditer(text):
                left[_clean(f"{m.group(1)}{needle}")] += 1
                hit = True
            for m in right_re.finditer(text):
                right[_clean(f"{needle}{m.group(1)}")] += 1
                hit = True
            if hit:
                hit_acts += 1

        self.stdout.write(f"\n  term {term!r} ({kind}) — literal in {hit_acts} act(s)")
        if not hit_acts:
            # Concept terms match through the Portuguese stemmer, so an act can
            # match "licitação" while containing only "licitações".
            self.stdout.write("    no literal occurrences (matched via stemming)")
            return
        for label, counter in (("preceded by", left), ("followed by", right)):
            top_n = [(p, n) for p, n in counter.most_common(top) if n > 1]
            if not top_n:
                continue
            self.stdout.write(f"    {label}:")
            for phrase, n in top_n:
                self.stdout.write(f"      {n:>4}  {phrase}")


def _clean(phrase: str) -> str:
    return re.sub(r"\s+", " ", phrase).strip(" .,;:-")
