"""The one place a category label is written.

The stored values stay English -- they are a storage enum, not a user-facing
string (decision-002). Only the labels are Portuguese, and they live here so
the digest email, the match API payload and the SPA filter cannot drift apart
the way they did when the SPA carried its own copy.
"""

# Insertion order is the order the SPA renders the filter dropdown in. It
# matches what web/src/lib/constants.ts shipped, so the dropdown does not
# reshuffle under the user.
CATEGORY_LABELS: dict[str, str] = {
    "tender": "licitação",
    "grant": "fomento",
    "appointment": "pessoal",
    "penalty": "sanção",
    "regulation": "norma",
    "other": "outro",
}

CATEGORIES: frozenset[str] = frozenset(CATEGORY_LABELS)

# An unenriched match carries "" -- the absence of a category, not the "other"
# category. Labelling it "outro" would claim the enricher looked at the act and
# found nothing in particular, which is a different and false statement.
NO_CATEGORY_LABEL = "sem categoria"


def label_for(value: str) -> str:
    """Portuguese label for a stored category value.

    An unrecognised value is returned unchanged. Both LLM clients coerce an
    unknown reply to "other" before it is stored, so this is a can't-happen;
    surfacing the raw value makes a data bug visible rather than disguising it
    as a real category.
    """
    if not value:
        return NO_CATEGORY_LABEL
    return CATEGORY_LABELS.get(value, value)
