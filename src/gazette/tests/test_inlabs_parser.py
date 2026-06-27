import datetime
from pathlib import Path

from gazette.inlabs.parser import ParsedArticle, parse_article

FIXTURES = Path(__file__).parent / "fixtures" / "dou"


def _fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_article_maps_every_field():
    parsed = parse_article(_fixture("do1_portaria_50000041.xml"))

    assert isinstance(parsed, ParsedArticle)
    assert parsed.date == datetime.date(2026, 6, 26)
    assert parsed.section == "DO1"

    item = parsed.item
    assert item.identifier == "50000041"
    # Identifica is stripped of leading/trailing whitespace, not the fallback.
    assert item.title.startswith("PORTARIA SE/MDA")
    assert item.title == item.title.strip()
    assert item.agency == (
        "Ministério do Desenvolvimento Agrário e Agricultura Familiar/"
        "Secretaria Executiva"
    )
    # pdfPage is a URL with &amp; unescaped to & by the XML parser.
    assert item.source_anchor.startswith("http://pesquisa.in.gov.br/")
    assert "&jornal=515" in item.source_anchor
    assert "&amp;" not in item.source_anchor
    # raw_text is plain text: HTML stripped, whitespace collapsed.
    assert "Plano Diretor de Logística Sustentável" in item.raw_text
    assert "ERIC MOURA" in item.raw_text
    assert "<p" not in item.raw_text
    assert "  " not in item.raw_text


def test_parse_article_falls_back_to_arttype_and_id_when_identifica_empty():
    xml = (
        b'<xml><article id="99999" pubName="DO3" artType="Edital" '
        b'pubDate="26/06/2026" artCategory="Org X" '
        b'pdfPage="http://x/p?a=1&amp;b=2"><body>'
        b'<Identifica/>'
        b'<Texto><![CDATA[<p>Conteudo  do edital.</p>]]></Texto>'
        b"</body></article></xml>"
    )
    parsed = parse_article(xml)

    assert parsed.item.identifier == "99999"
    assert parsed.item.title == "Edital 99999"          # fallback "{artType} {id}"
    assert parsed.item.raw_text == "Conteudo do edital."  # collapsed + stripped
    assert parsed.item.source_anchor == "http://x/p?a=1&b=2"
    assert parsed.section == "DO3"


def test_parse_article_handles_retificacao_with_empty_ementa():
    # Real edge case: Identifica present ("RETIFICAÇÃO"), Ementa self-closed.
    parsed = parse_article(_fixture("do1_retificacao_50004579.xml"))
    assert parsed.item.identifier == "50004579"
    assert parsed.item.title == "RETIFICAÇÃO"
    assert "DECRETO LEGISLATIVO" in parsed.item.raw_text
