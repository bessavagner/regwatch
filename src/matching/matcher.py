from functools import reduce
from operator import and_
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from gazette.models import Act, Edition
from gazette.normalize import normalize_text
from watches.models import Watch
from matching.models import Match


def _query_for(watch: Watch) -> SearchQuery | None:
    terms = [normalize_text(t) for t in watch.terms if t.strip()]
    if not terms:
        return None
    query = reduce(and_, (SearchQuery(t, config="simple", search_type="phrase") for t in terms))
    for ex in watch.exclude:
        ex = normalize_text(ex)
        if ex:
            query &= ~SearchQuery(ex, config="simple", search_type="phrase")
    return query


def match_edition(edition: Edition) -> list[Match]:
    created: list[Match] = []
    acts = Act.objects.filter(edition=edition)
    for watch in Watch.objects.filter(active=True).select_related("client"):
        query = _query_for(watch)
        if query is None:
            continue
        hits = (
            acts.annotate(rank=SearchRank(SearchVector("search_text", config="simple"), query))
            .filter(search_vector=query)
        )
        for act in hits:
            match, was_created = Match.objects.get_or_create(
                watch=watch, act=act,
                defaults={"rank": act.rank, "snippet": act.raw_text[:280]},
            )
            if was_created:
                created.append(match)
    return created
