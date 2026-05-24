from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
from xml.etree import ElementTree

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RawDocument


@dataclass(frozen=True)
class RssIngestionResult:
    created: int
    skipped_duplicates: int


@dataclass(frozen=True)
class RssItem:
    title: str
    link: str | None
    description: str | None
    published_at: datetime | None


def ingest_rss_xml(db: Session, source_id: int, rss_xml: str, company_id: int | None = None) -> RssIngestionResult:
    created = 0
    skipped_duplicates = 0

    for item in parse_rss_items(rss_xml):
        content_hash = build_rss_content_hash(item)
        existing = db.scalar(select(RawDocument).where(RawDocument.content_hash == content_hash))
        if existing is not None:
            skipped_duplicates += 1
            continue

        db.add(
            RawDocument(
                company_id=company_id,
                source_id=source_id,
                document_type="rss_item",
                title=item.title,
                url=item.link,
                published_at=item.published_at,
                raw_text=item.description,
                raw_payload_json={
                    "source_kind": "rss",
                    "title": item.title,
                    "link": item.link,
                    "description": item.description,
                },
                content_hash=content_hash,
            )
        )
        created += 1

    db.commit()
    return RssIngestionResult(created=created, skipped_duplicates=skipped_duplicates)


def parse_rss_items(rss_xml: str) -> list[RssItem]:
    root = ElementTree.fromstring(rss_xml)
    items: list[RssItem] = []

    for item in root.findall(".//item"):
        title = _node_text(item, "title")
        if not title:
            continue
        items.append(
            RssItem(
                title=title,
                link=_node_text(item, "link"),
                description=_node_text(item, "description"),
                published_at=_parse_pub_date(_node_text(item, "pubDate")),
            )
        )

    return items


def build_rss_content_hash(item: RssItem) -> str:
    stable_parts = [item.title, item.link or "", item.description or ""]
    return sha256("|".join(stable_parts).encode("utf-8")).hexdigest()


def _node_text(parent: ElementTree.Element, name: str) -> str | None:
    node = parent.find(name)
    if node is None or node.text is None:
        return None
    text = node.text.strip()
    return text or None


def _parse_pub_date(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
