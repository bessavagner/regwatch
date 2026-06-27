# src/gazette/inlabs/fetch.py
import datetime
import hashlib
import logging

from gazette.contracts import RawEdition
from gazette.inlabs.client import InlabsClient
from gazette.inlabs.parser import parse_section_zip

logger = logging.getLogger(__name__)

SECTIONS = ("DO1", "DO2", "DO3", "DO1E", "DO2E", "DO3E")


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_editions(
    date: datetime.date, *, client: InlabsClient | None = None
) -> list[RawEdition]:
    owns_client = client is None
    client = client or InlabsClient.from_env()
    try:
        client.login()
        editions: list[RawEdition] = []
        for section in SECTIONS:
            try:
                zip_bytes = client.download_section(date, section)
                if zip_bytes is None:
                    continue
                editions.append(
                    parse_section_zip(
                        zip_bytes, source_url=client.section_url(date, section)
                    )
                )
            except Exception:
                logger.exception("section %s failed for %s — skipping", section, date)
                continue
        return editions
    finally:
        if owns_client:
            client.close()
