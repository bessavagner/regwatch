import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class RawItem:
    identifier: str
    title: str
    agency: str
    raw_text: str
    source_anchor: str


@dataclass(frozen=True)
class RawEdition:
    date: datetime.date
    section: str
    source_url: str
    items: tuple[RawItem, ...]
