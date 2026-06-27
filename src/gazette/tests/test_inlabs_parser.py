import datetime
import io
import zipfile
from pathlib import Path

import pytest

from gazette.contracts import RawEdition
from gazette.inlabs.parser import ParsedArticle, parse_article, parse_section_zip

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
    assert parsed.section == "DO1"
    assert parsed.date == datetime.date(2026, 6, 26)


def test_parse_article_raises_clear_error_on_missing_pubdate():
    xml = (
        b'<xml><article id="123" pubName="DO1" artType="Portaria">'
        b'<body><Identifica>X</Identifica>'
        b'<Texto><![CDATA[<p>t</p>]]></Texto></body></article></xml>'
    )
    with pytest.raises(ValueError, match="pubDate"):
        parse_article(xml)


def _zip_of(*names: str, extra: dict[str, bytes] | None = None) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name in names:
            zf.writestr(name, _fixture(name))
        for fname, data in (extra or {}).items():
            zf.writestr(fname, data)
    return buf.getvalue()


def test_parse_section_zip_builds_edition_skipping_non_xml():
    zip_bytes = _zip_of(
        "do1_portaria_50000041.xml",
        "do1_retificacao_50004579.xml",
        extra={"some_image.jpg": b"\xff\xd8\xff not xml"},
    )
    url = "https://inlabs.example/index.php?p=2026-06-26&dl=2026-06-26-DO1.zip"

    edition = parse_section_zip(zip_bytes, source_url=url)

    assert isinstance(edition, RawEdition)
    assert edition.date == datetime.date(2026, 6, 26)
    assert edition.section == "DO1"
    assert edition.source_url == url
    assert len(edition.items) == 2  # the .jpg member is ignored
    assert {i.identifier for i in edition.items} == {"50000041", "50004579"}


def test_parse_section_zip_skips_unparseable_members():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("good.xml", _fixture("do1_portaria_50000041.xml"))
        zf.writestr("bad.xml", b"<xml><article></article></xml>")  # missing required attrs -> raises
    edition = parse_section_zip(buf.getvalue(), source_url="https://x/DO1.zip")
    assert {i.identifier for i in edition.items} == {"50000041"}   # good item survives, bad skipped
