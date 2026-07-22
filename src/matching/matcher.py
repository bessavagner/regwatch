from functools import reduce
from operator import or_

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q

from gazette.models import Act, Edition
from gazette.normalize import normalize_text
from watches.grouping import iter_terms, term_texts
from watches.models import Watch
from matching.models import Match


def _fts(text: str) -> SearchQuery:
    return SearchQuery(normalize_text(text), config="simple", search_type="phrase")


def _term_q(text: str, kind: str) -> Q:
    # Phase 1: both kinds resolve to the same simple-config phrase match. Kind is
    # recorded but not yet honoured, so this deploy changes only AND/OR structure.
    return Q(search_vector=_fts(text))


def _group_q(group) -> Q | None:
    if not isinstance(group, dict):
        return None
    parts = [
        _term_q(text, kind)
        for text, kind in iter_terms([group])
    ]
    if not parts:
        return None
    return reduce(or_, parts)


def _watch_q(watch: Watch) -> Q | None:
    """Build the filter for a watch, or None when it can never match.

    Fails closed: a watch with no groups, or any group with no usable terms,
    matches nothing rather than everything.
    """
    groups = watch.groups or []
    if not groups:
        return None
    query = Q()
    for group in groups:
        group_q = _group_q(group)
        if group_q is None:
            return None
        query &= group_q
    for ex in watch.exclude or []:
        ex = (ex or "").strip()
        if ex:
            query &= ~Q(search_vector=_fts(ex))
    return query


def _rank_query(watch: Watch) -> SearchQuery:
    # Advisory only. Ranking cannot span a mix of ILIKE and full-text predicates,
    # so this ORs every term as a full-text query purely to order results.
    return reduce(or_, (_fts(t) for t in term_texts(watch.groups)))


def match_edition(edition: Edition) -> list[Match]:
    created: list[Match] = []
    acts = Act.objects.filter(edition=edition)
    for watch in Watch.objects.filter(active=True).select_related("client"):
        if watch.section and watch.section != edition.section:
            continue
        query = _watch_q(watch)
        if query is None:
            continue
        hits = acts.annotate(
            rank=SearchRank(SearchVector("search_text", config="simple"), _rank_query(watch))
        ).filter(query)
        for act in hits:
            match, was_created = Match.objects.get_or_create(
                watch=watch, act=act,
                defaults={"rank": act.rank, "snippet": act.raw_text[:280]},
            )
            if was_created:
                created.append(match)
    return created
