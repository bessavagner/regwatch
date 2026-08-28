import logging
from functools import reduce
from operator import or_

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import BooleanField, ExpressionWrapper, F, Q

from gazette.models import Act, Edition
from gazette.normalize import normalize_pt, normalize_text
from watches.grouping import KIND_CONCEPT, KIND_ENTITY, MIN_SUBSTRING_LEN, iter_terms, term_texts
from watches.models import Watch
from matching.models import Match
from matching.snippet import build_snippet

logger = logging.getLogger(__name__)


def _pt(text: str) -> SearchQuery:
    return SearchQuery(normalize_pt(text), config="portuguese", search_type="phrase")


def _term_q(text: str, kind: str) -> Q:
    if kind == KIND_CONCEPT:
        return Q(search_vector_pt=_pt(text))
    folded = normalize_text(text)
    if len(folded) < MIN_SUBSTRING_LEN:
        # Too short to substring safely: 'ifc' would match inside 'ifce'.
        return Q(search_vector_pt=_pt(text))
    # __contains, not __icontains: Django compiles __icontains to
    # UPPER(search_text) LIKE UPPER(%pattern%), and that UPPER() wrapper makes
    # the predicate non-sargable against the gin_trgm_ops index on the bare
    # column, forcing a sequential scan over every act. Case-insensitivity is
    # already guaranteed on both sides by normalize_text, which lowercases
    # both search_text and folded, so __icontains would buy nothing anyway.
    return Q(search_text__contains=folded)


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
        if not isinstance(ex, str):
            continue
        ex = ex.strip()
        if ex:
            # Excludes are always evaluated with entity (substring) semantics,
            # which is at least as broad as the entity inclusion it suppresses.
            # It is NOT guaranteed to be as broad as a stemmed concept
            # inclusion: 'licitação' (concept) matches 'licitações' via
            # stemming, but the folded exclude 'licitacao' is not a substring
            # of 'licitacoes', so a concept inclusion can out-reach its
            # exclusion.
            query &= ~_term_q(ex, KIND_ENTITY)
    return query


def _rank_query(watch: Watch) -> SearchQuery:
    # Advisory only. It ORs every term across all groups as a full-text query
    # purely to order results, so it no longer reflects the AND/OR group
    # structure used to decide whether a watch matches. It will also need to
    # change once entity terms gain trigram/ILIKE substring matching, since
    # ranking cannot span a mix of ILIKE and full-text predicates.
    return reduce(or_, (_pt(t) for t in term_texts(watch.groups)))


def _term_annotations(terms) -> dict:
    """One boolean annotation per term, using the very predicate that matched.

    Re-deriving the fired terms in Python is not an option: a concept term
    matches through the Portuguese stemmer ('licitação' finds 'licitações'),
    which only Postgres can evaluate. Asking the database the same question it
    already answered is one extra expression per term over the same scan.
    """
    return {
        f"term_{i}": ExpressionWrapper(_term_q(text, kind), output_field=BooleanField())
        for i, (text, kind) in enumerate(terms)
    }


def _matched_terms(act, terms) -> list[str]:
    out: list[str] = []
    for i, (text, _) in enumerate(terms):
        if getattr(act, f"term_{i}", False) and text not in out:
            out.append(text)
    return out


def match_edition(edition: Edition) -> list[Match]:
    created: list[Match] = []
    acts = Act.objects.filter(edition=edition)
    for watch in Watch.objects.filter(active=True).select_related("client"):
        if watch.section and watch.section != edition.section:
            continue
        query = _watch_q(watch)
        if query is None:
            logger.warning(
                "watch %s (client %s) has no usable term groups; it will match nothing",
                watch.pk, watch.client.name,
            )
            continue
        terms = list(iter_terms(watch.groups))
        hits = acts.annotate(
            # The stored column, not a rebuilt vector: rebuilding recomputed a
            # full-body tsvector for every act on every watch (~20,000 per run
            # at six watches over ~3,400 acts) and, worse, omitted both the
            # NormalizeNFC wrapper and the agency that ingest applies -- so the
            # rank disagreed with the predicate that produced the match.
            rank=SearchRank(F("search_vector_pt"), _rank_query(watch)),
            **_term_annotations(terms),
        ).filter(query)
        for act in hits:
            matched = _matched_terms(act, terms)
            match, was_created = Match.objects.get_or_create(
                watch=watch, act=act,
                defaults={
                    "rank": act.rank,
                    "matched_terms": matched,
                    "snippet": build_snippet(act.raw_text, matched),
                },
            )
            if was_created:
                created.append(match)
    return created
