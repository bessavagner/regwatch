from gazette.normalize import normalize_text


def test_normalize_strips_accents_lowercases_and_collapses_whitespace():
    assert normalize_text("  PORTARIA   Nº 12 — Concessão  ") == "portaria no 12 — concessao"


def test_normalize_is_idempotent():
    once = normalize_text("Avaliação  Pública")
    assert normalize_text(once) == once
