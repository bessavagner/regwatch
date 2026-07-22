import re
import unicodedata


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
