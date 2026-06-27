import datetime
import re
from dataclasses import dataclass

from lxml import etree, html

from gazette.contracts import RawItem

_WS = re.compile(r"\s+")


@dataclass(frozen=True)
class ParsedArticle:
    item: RawItem
    date: datetime.date
    section: str


def _collapse(text: str) -> str:
    return _WS.sub(" ", text).strip()


def _plain_text(texto_html: str) -> str:
    # Texto holds escaped HTML; wrap so multiple <p> siblings have one root,
    # join pieces with spaces so adjacent paragraphs don't glue together.
    fragment = html.fragment_fromstring(texto_html, create_parent="div")
    pieces = [t for t in fragment.itertext() if t.strip()]
    return _collapse(" ".join(pieces))


def parse_article(xml_bytes: bytes) -> ParsedArticle:
    root = etree.fromstring(xml_bytes)
    article = root if root.tag == "article" else root.find("article")

    article_id = article.get("id")
    art_type = article.get("artType", "").strip()

    identifica_el = article.find("body/Identifica")
    identifica = (identifica_el.text or "").strip() if identifica_el is not None else ""
    title = identifica or f"{art_type} {article_id}".strip()

    texto_el = article.find("body/Texto")
    raw_text = _plain_text(texto_el.text or "") if texto_el is not None else ""

    item = RawItem(
        identifier=article_id,
        title=title,
        agency=article.get("artCategory", "").strip(),
        raw_text=raw_text,
        source_anchor=article.get("pdfPage", ""),
    )
    pub_date = datetime.datetime.strptime(article.get("pubDate"), "%d/%m/%Y").date()
    return ParsedArticle(item=item, date=pub_date, section=article.get("pubName"))
