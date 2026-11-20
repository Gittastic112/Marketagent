"""Comparable stored closes, dated evidence and owner-scoped thesis annotations."""
import hashlib
import json
from bisect import bisect_left
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Company, Event, MarketPrice, RawDocument, Source, ThesisNote
from app.models.thesis_note import ThesisPricePin
from app.schemas.publication import document_publication
from app.schemas.price_timeline import DatedSource, PriceAnchor, PricePinCreate, PricePinRead, PricePoint, PriceSeries, PriceTimeline


WINDOW = 365
CONTEXT_LIMIT = 2000
THRESHOLD = 5
P = MarketPrice
SYMBOL = func.coalesce(P.provider_symbol, P.ticker)
BASIS = (P.provider_name, SYMBOL, P.currency, P.market, P.exchange, P.adjustment_state, P.claim_type)


def _digest(values) -> str:
    return hashlib.sha256(json.dumps(values, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()


def _series(provider, symbol, currency, market, exchange, adjustment, claim_type) -> PriceSeries:
    return PriceSeries(key=_digest([provider, symbol, currency, market, exchange, adjustment, claim_type]),
                       provider=provider, symbol=symbol, currency=currency, market=market,
                       exchange=exchange, adjustment=adjustment, claim_type=claim_type)


def _eligible(company_id: int):
    factual = and_(P.claim_type == "Fact", ~P.provider_name.ilike("%mock%"), ~P.provider_name.ilike("%sample%"),
                   ~P.provider_name.ilike("%fixture%"))
    return (P.company_id == company_id, P.price_type == "end_of_day", P.price > 0,
            or_(factual, P.claim_type == "Mock Data"))


def _basis_filter(series: PriceSeries):
    values = (series.provider, series.symbol, series.currency, series.market, series.exchange, series.adjustment, series.claim_type)
    return tuple(column == value for column, value in zip(BASIS, values, strict=True))


def _anchor(price: MarketPrice, series: PriceSeries):
    close = format(price.price, ".6f")
    fingerprint = _digest([price.id, price.company_id, price.as_of_date.isoformat(), series.key, close])
    anchor = PriceAnchor(**series.model_dump(), price_id=price.id, date=price.as_of_date, price=close,
                         observed_at=price.observed_at, source_timestamp=price.source_timestamp)
    return fingerprint, anchor


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _dated_context(db, company_id, market, points):
    zone = ZoneInfo({"US": "America/New_York", "IN": "Asia/Kolkata"}.get(market, "UTC"))
    low = datetime.combine(min(points) - timedelta(days=1), time.min, timezone.utc)
    high = datetime.combine(max(points) + timedelta(days=2), time.min, timezone.utc)
    columns = (RawDocument.id, RawDocument.title, RawDocument.document_type,
               RawDocument.published_at, Source.name, RawDocument.raw_payload_json["source_kind"].as_string(),
               RawDocument.raw_payload_json["publication_precision"].as_string())
    docs = (select(*columns).join(Source, Source.id == RawDocument.source_id)
            .where(RawDocument.company_id == company_id, RawDocument.published_at >= low,
                   RawDocument.published_at < high).order_by(RawDocument.published_at.desc(), RawDocument.id))
    events = (select(*columns, Event.id, Event.title, Event.event_time, func.substr(Event.description, 1, 450))
              .join(Source, Source.id == RawDocument.source_id).join(Event, Event.raw_document_id == RawDocument.id)
              .where(RawDocument.company_id == company_id, Event.company_id == company_id,
                     RawDocument.published_at.is_not(None), Event.event_time >= low, Event.event_time < high)
              .order_by(Event.event_time.desc(), Event.id))
    limited = False
    dates = sorted(points)
    for query, is_event in ((docs, False), (events, True)):
        rows = db.execute(query.limit(CONTEXT_LIMIT + 1)).all()
        limited |= len(rows) > CONTEXT_LIMIT
        for row in rows[:CONTEXT_LIMIT]:
            document_id, title, kind, published, source, source_kind, precision = row[:7]
            published = _utc(published)
            publication = document_publication(published, kind, source_kind, precision)
            date_only = not isinstance(publication, datetime)
            publication_day = publication if date_only else publication.astimezone(zone).date()
            event_id = None
            summary = None
            day = publication_day
            label = title
            if is_event:
                event_id, label, event_time, summary = row[7:]
                # A filing's date-only midnight is an archival convention.
                stamp = _utc(event_time)
                day = publication_day if date_only and stamp == published else stamp.astimezone(zone).date()
                if day < publication_day:
                    continue
            position = bisect_left(dates, day)
            if position == len(dates):
                continue
            target = dates[position]
            # Include releases between two close dates, retaining the actual source date.
            if day != target and (position == 0 or target - dates[position - 1] > timedelta(days=7)):
                continue
            sample = any(term in f"{source} {title} {label}".lower() for term in ("sample", "mock", "fixture"))
            points[target].sources.append(DatedSource(
                document_id=document_id, title=label, source=source, event_id=event_id, summary=summary,
                context_date=day,
                published=publication_day.isoformat() if date_only else published.isoformat(), sample=sample,
            ))
    return limited


def company_timeline(db: Session, company_id: int, owner: str, key: str | None, through: date | None):
    if db.scalar(select(Company.id).where(Company.id == company_id)) is None:
        raise HTTPException(404, "Company not found")
    eligible = _eligible(company_id)
    grouped = db.execute(select(*BASIS, func.count(distinct(P.as_of_date)), func.max(P.as_of_date))
                         .where(*eligible).group_by(*BASIS)).all()
    # Coverage wins first, then recency. The stable key breaks remaining ties.
    choices = sorted(((_series(*row[:-2]), row[-2], row[-1]) for row in grouped),
                     key=lambda item: (item[0].claim_type != "Fact", -item[1], -item[2].toordinal(), item[0].key))
    result = PriceTimeline(choices=[item[0] for item in choices], move_threshold_pct=THRESHOLD)
    if key is not None and not any(s.key == key for s in result.choices):
        raise HTTPException(404, "This stored price series is unavailable")
    if not choices:
        return result
    series = next(s for s in result.choices if not key or s.key == key)
    result.series = series
    filters = (*eligible, *_basis_filter(series))
    days = select(P.as_of_date).where(*filters).distinct().order_by(P.as_of_date.desc())
    if through:
        days = days.where(P.as_of_date <= through)
    dates = list(db.scalars(days.limit(WINDOW + 1)))
    result.truncated = len(dates) > WINDOW
    if not dates:
        return result
    by_day = defaultdict(list)
    rows = db.scalars(select(P).where(*filters, P.as_of_date.in_(dates[:WINDOW])).order_by(P.as_of_date, P.id))
    for row in rows:
        by_day[row.as_of_date].append(row)
    points = {}
    by_fingerprint = {}
    previous = None
    for day, observations in by_day.items():
        point = PricePoint(date=day)
        points[day] = point
        if len({p.price for p in observations}) != 1:
            previous = None
            continue
        current = observations[0]
        point.price = float(current.price)
        point.price_id = current.id
        point.fingerprint, _ = _anchor(current, series)
        by_fingerprint[point.fingerprint] = point
        if previous:
            point.gap_before = day - previous.as_of_date > timedelta(days=7)
            if not point.gap_before and series.adjustment in {"unadjusted", "adjusted", "split_adjusted"}:
                change = (current.price / previous.price - 1) * Decimal(100)
                point.previous_date = previous.as_of_date
                point.change_pct = float(change)
                point.large_move = abs(change) >= THRESHOLD
        previous = current
    result.context_limited = _dated_context(db, company_id, series.market, points)
    if by_fingerprint:
        pins = db.scalars(select(ThesisPricePin).join(ThesisNote)
                          .where(ThesisNote.user_id == owner, ThesisPricePin.company_id == company_id,
                                 ThesisPricePin.fingerprint.in_(by_fingerprint)).order_by(ThesisPricePin.id))
        for pin in pins:
            by_fingerprint[pin.fingerprint].pins.append(PricePinRead.model_validate(pin))
    result.points = list(points.values())
    return result


def thesis_pins(db, thesis_id: int, owner: str):
    if db.scalar(select(ThesisNote.id).where(ThesisNote.id == thesis_id, ThesisNote.user_id == owner)) is None:
        raise HTTPException(404, "Thesis not found")
    return list(db.scalars(select(ThesisPricePin).where(ThesisPricePin.thesis_note_id == thesis_id)
                           .order_by(ThesisPricePin.id.desc())))


def save_pin(db: Session, company_id: int, owner: str, payload: PricePinCreate):
    thesis = db.scalar(select(ThesisNote.id).where(ThesisNote.id == payload.thesis_id,
                       ThesisNote.user_id == owner, ThesisNote.company_id == company_id).with_for_update())
    if thesis is None:
        raise HTTPException(404, "Thesis not found for this company")
    request = select(ThesisPricePin).where(ThesisPricePin.thesis_note_id == thesis,
                                          ThesisPricePin.request_id == str(payload.request_id))

    def existing_pin():
        existing = db.scalar(request)
        if existing and (existing.fingerprint != payload.fingerprint or existing.anchor["price_id"] != payload.price_id
                         or existing.text != payload.text):
            raise HTTPException(409, "This save already belongs to a different note")
        return existing

    if previous := existing_pin():
        return previous
    price = db.scalar(select(P).where(*_eligible(company_id), P.id == payload.price_id).with_for_update())
    if price is None:
        raise HTTPException(404, "Stored closing price not found")
    series = _series(price.provider_name, price.provider_symbol or price.ticker, price.currency,
                     price.market, price.exchange, price.adjustment_state, price.claim_type)
    fingerprint, anchor = _anchor(price, series)
    conflict = db.scalar(select(P.id).where(*_eligible(company_id), *_basis_filter(series),
                         P.as_of_date == price.as_of_date, P.price != price.price).limit(1))
    if fingerprint != payload.fingerprint or conflict is not None:
        raise HTTPException(409, "The closing price changed. Reload the chart and review the point.")
    pin = ThesisPricePin(thesis_note_id=thesis, company_id=company_id, request_id=str(payload.request_id),
                         fingerprint=fingerprint, anchor=anchor.model_dump(mode="json"), text=payload.text)
    db.add(pin)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if previous := existing_pin():
            return previous
        raise
    return pin
