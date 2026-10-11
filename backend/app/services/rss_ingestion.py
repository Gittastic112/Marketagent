from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
import logging
from re import escape, search, sub
from typing import Any, Callable
from xml.etree.ElementTree import Element
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import validate_safe_url
from app.models import Company, RawDocument, Source

COMMON_COMPANY_MATCH_TERMS = {
    "ai",
    "cloud",
    "data",
    "global",
    "group",
    "holdings",
    "industrial",
    "market",
    "systems",
    "technology",
}
logger = logging.getLogger(__name__)
LEGAL_SUFFIXES = {
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "incorporated",
    "ltd",
    "plc",
}


@dataclass(frozen=True)
class RssIngestionResult:
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    error_count: int = 0
    errors: tuple[str, ...] = ()

    @property
    def created(self) -> int:
        return self.created_count

    @property
    def skipped_duplicates(self) -> int:
        return self.skipped_duplicate_count


@dataclass(frozen=True)
class RssItem:
    title: str
    link: str | None
    description: str | None
    published_at: datetime | None
    pub_date_raw: str | None = None


def ingest_rss_xml(db: Session, source_id: int, rss_xml: str, company_id: int | None = None) -> RssIngestionResult:
    created = 0
    skipped_duplicates = 0
    errors: list[str] = []
    source = db.get(Source, source_id)

    try:
        items = parse_rss_items(rss_xml)
    except (ElementTree.ParseError, DefusedXmlException) as exc:
        logger.error(
            "RSS payload parsing failed",
            extra={"provider": "rss", "exception_type": type(exc).__name__},
        )
        return RssIngestionResult(
            fetched_count=0,
            created_count=0,
            skipped_duplicate_count=0,
            error_count=1,
            errors=("RSS payload is not valid XML.",),
        )

    for item in items:
        content_hash = build_rss_content_hash(item)
        existing = _find_existing_raw_document(db, content_hash, item.link)
        if existing is not None:
            skipped_duplicates += 1
            continue

        linked_company_id = company_id if company_id is not None else _infer_company_id(db, item)
        db.add(
            RawDocument(
                company_id=linked_company_id,
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
                    "pubDate": item.pub_date_raw,
                    "source_name": source.name if source else None,
                },
                content_hash=content_hash,
            )
        )
        created += 1

    db.commit()
    return RssIngestionResult(
        fetched_count=len(items),
        created_count=created,
        skipped_duplicate_count=skipped_duplicates,
        error_count=len(errors),
        errors=tuple(errors),
    )


def ingest_rss_feed_url(
    db: Session,
    source_id: int,
    feed_url: str | None = None,
    company_id: int | None = None,
    http_get: Callable[..., Any] | None = None,
) -> RssIngestionResult:
    source = db.get(Source, source_id)
    url = feed_url or (source.base_url if source else None)
    if not url:
        return RssIngestionResult(
            fetched_count=0,
            created_count=0,
            skipped_duplicate_count=0,
            error_count=1,
            errors=("RSS feed URL is required",),
        )

    try:
        if http_get is not None:
            validate_safe_url(url)
            response = http_get(url, timeout=20)
            response.raise_for_status()
            xml_text = response.text
        else:
            from app.providers.rss_provider import RSSProvider
            provider = RSSProvider()
            xml_text = provider.fetch_feed_xml(url)
    except Exception as exc:
        logger.error(
            "RSS feed fetch failed",
            extra={"provider": "rss", "exception_type": type(exc).__name__},
        )
        return RssIngestionResult(
            fetched_count=0,
            created_count=0,
            skipped_duplicate_count=0,
            error_count=1,
            errors=("RSS provider could not fetch the feed.",),
        )

    return ingest_rss_xml(db, source_id=source_id, rss_xml=xml_text, company_id=company_id)


def parse_rss_items(rss_xml: str) -> list[RssItem]:
    if len(rss_xml.encode("utf-8")) > 4 * 1024 * 1024:
        raise ElementTree.ParseError("RSS payload exceeds the size limit.")
    root = ElementTree.fromstring(rss_xml, forbid_dtd=True)
    items: list[RssItem] = []

    for item in root.findall(".//item"):
        title = _node_text(item, "title")
        if not title:
            continue
        pub_date_raw = _node_text(item, "pubDate")
        items.append(
            RssItem(
                title=title,
                link=_node_text(item, "link"),
                description=_node_text(item, "description"),
                published_at=_parse_pub_date(pub_date_raw),
                pub_date_raw=pub_date_raw,
            )
        )

    return items


def build_rss_content_hash(item: RssItem) -> str:
    stable_parts = [item.title, item.link or "", item.description or ""]
    return sha256("|".join(stable_parts).encode("utf-8")).hexdigest()


def _find_existing_raw_document(db: Session, content_hash: str, url: str | None) -> RawDocument | None:
    filters = [RawDocument.content_hash == content_hash]
    if url:
        filters.append(RawDocument.url == url)
    return db.scalar(select(RawDocument).where(or_(*filters)))


def _infer_company_id(db: Session, item: RssItem) -> int | None:
    text = f"{item.title} {item.description or ''}".lower()
    companies = list(db.scalars(select(Company).where(Company.active.is_(True))))
    matches: set[int] = set()

    for company in companies:
        if any(_term_matches(text, term) for term in _company_match_terms(company)):
            matches.add(company.id)

    if len(matches) == 1:
        return next(iter(matches))
    return None


def _company_match_terms(company: Company) -> list[str]:
    terms = [company.ticker, company.name, _simplified_company_name(company.name)]
    terms.extend(company.aliases_json or [])
    deduped_terms: list[str] = []
    for term in terms:
        normalized = _normalize_match_term(term)
        if not normalized or normalized in deduped_terms:
            continue
        if normalized in COMMON_COMPANY_MATCH_TERMS:
            continue
        deduped_terms.append(normalized)
    return deduped_terms


def _simplified_company_name(name: str) -> str:
    words = [_normalize_match_term(word) for word in name.split()]
    meaningful_words = [word for word in words if word and word not in LEGAL_SUFFIXES]
    return " ".join(meaningful_words)


def _normalize_match_term(term: object) -> str:
    text = sub(r"[^a-zA-Z0-9 ]+", " ", str(term).lower())
    return " ".join(text.split())


def _term_matches(text: str, term: str) -> bool:
    return bool(search(rf"\b{escape(term)}\b", text))


def _node_text(parent: Element, name: str) -> str | None:
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
