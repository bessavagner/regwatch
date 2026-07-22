import re
import unicodedata

from django.db.models import Func, TextField


class NormalizeNFC(Func):
    """Postgres normalize(x, NFC) (PG13+).

    NFC is a keyword there, not a string literal, so a plain Func call
    would quote it wrong — hence the custom template. Used to build
    Act.search_vector_pt so the index agrees with normalize_pt(), which
    NFC-normalises queries: some upstream gazette text arrives NFD
    (accents as combining characters), and an un-normalised index
    silently fails to match text that is actually present.
    """

    function = "NORMALIZE"
    template = "%(function)s(%(expressions)s, NFC)"
    output_field = TextField()


def normalize_text(s: str) -> str:
    s = s.lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_pt(s: str) -> str:
    """Lowercase and collapse whitespace, preserving accents.

    Deliberately does NOT strip accents. Measured: with accents removed,
    'licitações' stems to 'licitaco' and 'licitação' to 'licitaca', so the two
    stop matching. Accented, both stem to 'licit'.
    """
    s = unicodedata.normalize("NFC", s.lower())
    return re.sub(r"\s+", " ", s).strip()
