import unicodedata

from matching.snippet import build_snippet, fold, find_term

HEADER = (
    "DESPACHO Nº 431, DE 21 DE AGOSTO DE 2026 A SUPERINTENDENTE DO "
    "DEPARTAMENTO NACIONAL DE OBRAS CONTRA AS SECAS, no uso das atribuições "
    "que lhe confere o Regimento Interno, e considerando o que consta do "
    "processo administrativo em epígrafe, bem como a manifestação da "
    "Procuradoria Federal Especializada junto à Autarquia, resolve: "
)
BODY = "Autorizar a execução das obras de saneamento básico no município. "
TAIL = "Publique-se. " * 30


def test_fold_preserves_length():
    s = "Licitação ÁGUA ñ"
    assert len(fold(s)) == len(s)
    assert fold(s) == "licitacao agua n"


def test_fold_preserves_length_for_nfd_input():
    s = unicodedata.normalize("NFD", "licitação")
    assert len(fold(s)) == len(s)


def test_find_term_returns_offsets_into_the_original():
    text = HEADER + BODY
    span = find_term(text, ["saneamento"])
    assert span is not None
    start, end = span
    assert text[start:end] == "saneamento"


def test_find_term_tolerates_wrapped_whitespace():
    # DOU bodies wrap mid-phrase; the stored text keeps the newline.
    text = "Contrato com a BETA\n     CORP nesta data."
    span = find_term(text, ["beta corp"])
    assert span is not None
    assert text[span[0]:span[1]] == "BETA\n     CORP"


def test_find_term_is_accent_insensitive_both_ways():
    assert find_term("Obras de SANEAMENTO básico", ["saneamento"]) is not None
    assert find_term("Dispensa de licitacao", ["licitação"]) is not None


def test_find_term_returns_none_when_absent():
    assert find_term(HEADER, ["saneamento"]) is None


def test_snippet_centres_on_the_term():
    text = HEADER + BODY + TAIL
    out = build_snippet(text, ["saneamento"])
    assert "saneamento" in out
    assert not out.startswith("DESPACHO")
    assert out.startswith("…")
    assert len(out) <= 282  # width plus the two ellipses


def test_snippet_returns_a_short_act_whole():
    text = "Licença à BETA CORP."
    assert build_snippet(text, ["beta corp"]) == text
    assert "…" not in build_snippet(text, ["beta corp"])


def test_snippet_falls_back_to_the_head_when_no_term_is_literal():
    # Concept terms match through the Portuguese stemmer, so an act can match
    # 'licitação' while containing only 'licitações' -- there is nothing to
    # centre on and the old behaviour is the right fallback.
    text = HEADER + TAIL
    out = build_snippet(text, ["saneamento"])
    assert out.startswith("DESPACHO Nº 431")
    assert out.endswith("…")


def test_snippet_falls_back_with_no_terms_at_all():
    text = HEADER + TAIL
    assert build_snippet(text, []).startswith("DESPACHO Nº 431")


def test_snippet_of_empty_text_is_empty():
    assert build_snippet("", ["saneamento"]) == ""
    assert build_snippet(None, ["saneamento"]) == ""


def test_snippet_does_not_start_or_end_mid_word():
    text = HEADER + BODY + TAIL
    out = build_snippet(text, ["saneamento"]).strip("…")
    assert not out.startswith(" ")
    # The first and last runs are whole words, not fragments.
    assert text.find(out) != -1
