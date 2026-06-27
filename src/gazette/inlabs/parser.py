import datetime
import io
import logging
import re
import zipfile
from dataclasses import dataclass

from lxml import etree, html

from gazette.contracts import RawEdition, RawItem

logger = logging.getLogger(__name__)

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

    # Validate required attributes
    article_id = article.get("id")
    pub_date = article.get("pubDate")
    pub_name = article.get("pubName")

    missing = []
    if not article_id:
        missing.append("id")
    if not pub_date:
        missing.append("pubDate")
    if not pub_name:
        missing.append("pubName")

    if missing:
        article_id_info = f" (article id: {article_id})" if article_id else ""
        raise ValueError(
            f"DOU article missing required attribute(s): {', '.join(missing)}{article_id_info}"
        )

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
    pub_date_obj = datetime.datetime.strptime(pub_date, "%d/%m/%Y").date()
    return ParsedArticle(item=item, date=pub_date_obj, section=pub_name)


def parse_section_zip(zip_bytes: bytes, *, source_url: str) -> RawEdition:
    items = []
    date = None
    section = None
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in sorted(zf.namelist()):
            if not name.lower().endswith(".xml"):
                continue
            try:
                parsed = parse_article(zf.read(name))
            except Exception:
                logger.warning("skipping unparseable member %s in %s", name, source_url)
                continue
            items.append(parsed.item)
            date = parsed.date
            section = parsed.section
    return RawEdition(
        date=date, section=section, source_url=source_url, items=tuple(items)
    )
