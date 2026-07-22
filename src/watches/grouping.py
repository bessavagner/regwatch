"""Helpers for the Watch.groups structure.

A watch holds a list of groups. Groups are ANDed; the terms inside one group are
ORed. Each term is {"text": str, "kind": "entity" | "concept"}.

Kept free of Django imports so the data migration can use it without dragging in
model state.
"""
from collections.abc import Iterator

KIND_ENTITY = "entity"
KIND_CONCEPT = "concept"
VALID_KINDS = (KIND_ENTITY, KIND_CONCEPT)

# Entity terms shorter than this fall back to whole-word matching, because a
# 3-character substring matches inside unrelated words.
MIN_SUBSTRING_LEN = 4


def groups_from_terms(terms: list, match_mode: str) -> list[dict]:
    """Convert the legacy terms + match_mode pair into groups, preserving meaning."""
    cleaned = [t.strip() for t in (terms or []) if isinstance(t, str) and t.strip()]
    if not cleaned:
        return []
    if match_mode == "any":
        return [{"terms": [{"text": t, "kind": KIND_ENTITY} for t in cleaned]}]
    return [{"terms": [{"text": t, "kind": KIND_ENTITY}]} for t in cleaned]


def iter_terms(groups) -> Iterator[tuple[str, str]]:
    """Yield (text, kind) for every non-blank term across every group."""
    for group in groups or []:
        if not isinstance(group, dict):
            continue
        for term in group.get("terms") or []:
            if not isinstance(term, dict):
                continue
            text = (term.get("text") or "").strip()
            if text:
                yield text, term.get("kind") or KIND_ENTITY


def term_texts(groups) -> list[str]:
    return [text for text, _ in iter_terms(groups)]
