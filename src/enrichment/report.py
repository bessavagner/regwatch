"""The numbers behind the D3 and D5 acceptance criteria.

Pure functions over sequences -- no model access -- so the metric that decides
whether a prompt change worked can be unit-tested without a database, and so
the *same* functions produce the before and the after. Written before the
prompt changes, deliberately: a metric written afterwards is a metric shaped to
the result it was meant to judge.
"""
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from gazette.normalize import normalize_text

# Six words is enough to separate "anuiu previamente a celebracao de contrato"
# from "declarou de utilidade publica a entidade" without splitting either on
# the party name that follows.
CLUSTER_WORDS = 6

# A two-act "cluster" that splits is an anecdote, not evidence of an
# inconsistent rubric.
MIN_CLUSTER = 3


def cluster_key(summary: str, words: int = CLUSTER_WORDS) -> str:
    """The first `words` normalised words of a summary.

    D3's evidence is phrased in exactly these terms: acts summarised "anuiu
    previamente a celebracao de contrato" split 12 regulation / 5 other. Two
    summaries that open the same way describe the same kind of act, so the
    opening is the cluster key.
    """
    return " ".join(normalize_text(summary or "").split()[:words])


@dataclass(frozen=True)
class Cluster:
    key: str
    categories: Counter

    @property
    def size(self) -> int:
        return sum(self.categories.values())

    @property
    def single_valued(self) -> bool:
        return len(self.categories) == 1


def cluster_summaries(
    rows: Iterable[tuple[str, str]], min_size: int = MIN_CLUSTER
) -> list[Cluster]:
    """Group (summary, category) pairs by opening phrase, largest cluster first."""
    buckets: dict[str, Counter] = {}
    for summary, category in rows:
        key = cluster_key(summary)
        if not key:
            continue
        buckets.setdefault(key, Counter())[category or ""] += 1
    clusters = [Cluster(key, counts) for key, counts in buckets.items()]
    return sorted(
        (c for c in clusters if c.size >= min_size), key=lambda c: (-c.size, c.key)
    )


def inconsistency_rate(clusters: list[Cluster]) -> float:
    """Share of clustered matches sitting in a cluster that splits.

    This is the number D3 moves: about 0.29 on Sertao before the rubric.
    """
    total = sum(c.size for c in clusters)
    if not total:
        return 0.0
    return sum(c.size for c in clusters if not c.single_valued) / total


def histogram(values: Iterable[object]) -> dict[object, int]:
    return dict(Counter(values))


def modal_share(hist: dict[object, int]) -> float:
    """Share of rows in the most common bucket. 1.0 means no spread at all.

    The one metric that compares the old confidence float against the new
    signal score on equal terms: confidence rounded to two places sits at
    0.98-0.99 for everything, so its modal share is near 1.0 and it cannot
    order a feed.
    """
    total = sum(hist.values())
    if not total:
        return 0.0
    return max(hist.values()) / total
