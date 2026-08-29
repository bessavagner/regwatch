"""Which of a watch's stored matches its *current* definition would not produce.

Editing a watch does not rewrite history: the rows created under the old terms
stay. That is usually harmless, but it makes any per-watch count a mix of two
term sets — which is exactly wrong when the count is being used to judge an
edit. Shared by prune_stale_matches and by backfill_watches, so an evaluation
cannot report a number the current definition disagrees with.
"""
import datetime

from gazette.models import Act
from matching.matcher import _watch_q
from matching.models import Match
from watches.models import Watch


def stale_match_ids(
    watch: Watch,
    *,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
) -> list[int]:
    """Ids of untriaged matches `watch` holds that it would no longer make.

    Only `state="new"`: a relevant/dismissed verdict is a human decision, and
    rewriting history under it would be worse than a stale row.
    """
    qs = Match.objects.filter(watch=watch, state="new")
    if date_from is not None:
        qs = qs.filter(act__edition__date__gte=date_from)
    if date_to is not None:
        qs = qs.filter(act__edition__date__lte=date_to)

    held = list(qs.values_list("id", "act_id"))
    if not held:
        return []

    query = _watch_q(watch)
    if query is None:
        # The watch can never match anything; every match it holds is stale.
        return [match_id for match_id, _ in held]

    keep = set(
        Act.objects.filter(query, id__in=[act_id for _, act_id in held])
        .values_list("id", flat=True)
    )
    return [match_id for match_id, act_id in held if act_id not in keep]
