from gazette.normalize import normalize_text, normalize_pt


def test_normalize_strips_accents_lowercases_and_collapses_whitespace():
    assert normalize_text("  PORTARIA   Nº 12 — Concessão  ") == "portaria no 12 — concessao"


def test_normalize_is_idempotent():
    once = normalize_text("Avaliação  Pública")
    assert normalize_text(once) == once


def test_normalize_pt_preserves_accents():
    # The Portuguese stemmer needs accents: stripped, 'licitação' and
    # 'licitações' stem to different roots and stop matching each other.
    assert normalize_pt("  LICITAÇÃO   Nº 3 ") == "licitação nº 3"
