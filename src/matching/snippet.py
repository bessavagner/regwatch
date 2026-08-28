"""Build the snippet a reader sees: the matched term, in its context.

Deliberately free of Django imports -- it is pure text and is unit-tested
without a database.

Why not reuse gazette.normalize.normalize_text: it NFKD-decomposes and
collapses whitespace, so 'á' becomes two characters and a run of spaces
becomes one. Every offset it produces is wrong by an unknown amount, and an
offset into the original string is the entire point here.
"""
import re
import unicodedata
from collections.abc import Iterable

WIDTH = 280
ELLIPSIS = "…"


def _fold_char(ch: str) -> str:
    decomposed = unicodedata.normalize("NFKD", ch.lower())
    base = "".join(c for c in decomposed if not unicodedata.combining(c))
    # Some case mappings expand ('İ'.lower() is two code points). Keep exactly
    # one character so offsets into the fold stay offsets into the original.
    return base[0] if base else ch


def fold(text: str) -> str:
    """Lowercase and strip accents, character for character."""
    return "".join(_fold_char(c) for c in text)


def _pattern(term: str) -> re.Pattern | None:
    tokens = [re.escape(t) for t in fold(term).split()]
    if not tokens:
        return None
    # Whitespace-flexible: DOU bodies wrap mid-phrase, so a stored act reads
    # 'BETA\n     CORP' where the watch says 'beta corp'.
    return re.compile(r"\s+".join(tokens))


def find_term(text: str, terms: Iterable[str]) -> tuple[int, int] | None:
    """Offsets of the first term that literally occurs, or None."""
    folded = fold(text)
    for term in terms:
        pattern = _pattern(term)
        if pattern is None:
            continue
        hit = pattern.search(folded)
        if hit:
            return hit.start(), hit.end()
    return None


def build_snippet(text: str, terms: Iterable[str], width: int = WIDTH) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    if len(text) <= width:
        # Short acts are shown whole: an ellipsis would announce a truncation
        # that did not happen.
        return text

    span = find_term(text, terms or [])
    if span is None:
        # Nothing literal to centre on -- a concept term matched through the
        # stemmer, or the act was matched on a field the body does not repeat.
        # The head of the act is the honest fallback and is what shipped before.
        return text[:width].rstrip() + ELLIPSIS

    start, end = span
    centre = (start + end) // 2
    left = max(0, centre - width // 2)
    right = min(len(text), left + width)
    left = max(0, right - width)

    # Snap to whitespace so the window neither starts nor ends mid-word. Both
    # searches are bounded by the term itself, so snapping can never eat it.
    if left > 0:
        space = text.find(" ", left, start)
        if space != -1:
            left = space + 1
    if right < len(text):
        space = text.rfind(" ", end, right)
        if space != -1:
            right = space

    out = text[left:right].strip()
    return (
        (ELLIPSIS if left > 0 else "")
        + out
        + (ELLIPSIS if right < len(text) else "")
    )
