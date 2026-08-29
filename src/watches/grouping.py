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


def group_from_spec(spec: str) -> dict:
    """Turn "concept:convênio|termo de fomento" into a groups entry.

    The kind prefix is optional and applies to every term in the group, which is
    how watches are actually written: a group is one dimension (the places, the
    funding words), and a dimension does not usually mix entity and concept
    semantics.

    Raises ValueError; the management commands turn that into a CommandError.
    Kept here so create_watch and update_watch cannot drift apart on the syntax.
    """
    kind = KIND_ENTITY
    body = spec
    head, sep, rest = spec.partition(":")
    if sep and head.strip().lower() in VALID_KINDS:
        kind, body = head.strip().lower(), rest
    elif sep and " " not in head and head.strip() and not head.strip().isdigit():
        # A prefix was clearly intended -- naming an unknown kind must not
        # silently fall through to entity and quietly change the semantics.
        raise ValueError(
            f"unknown term kind {head.strip()!r}; use one of {', '.join(VALID_KINDS)}"
        )

    terms = [{"text": t.strip(), "kind": kind} for t in body.split("|") if t.strip()]
    if not terms:
        raise ValueError(
            f"group {spec!r} has no terms; the matcher fails closed on an empty "
            "group, so the watch would match nothing while looking active"
        )
    return {"terms": terms}


def groups_from_specs(specs: list[str], joined: str = "") -> list[dict]:
    """Every group, from repeated --group flags and/or one ';'-joined --groups."""
    all_specs = list(specs) + [g for g in joined.split(";") if g.strip()]
    return [group_from_spec(s) for s in all_specs]
