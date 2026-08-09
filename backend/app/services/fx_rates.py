from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FxRateObservation


class FxRateUnavailable(ValueError):
    def __init__(self, base_currency: str, quote_currency: str, as_of_date: date):
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.as_of_date = as_of_date
        super().__init__(
            f"No FX observation is available for {base_currency}/{quote_currency} on or before {as_of_date}."
        )


@dataclass(frozen=True)
class FxConversionRate:
    base_currency: str
    quote_currency: str
    rate: Decimal
    as_of_date: date
    observation_id: int | None
    provider_name: str
    inverted: bool
    age_days: int
    is_stale: bool


def _latest_observation(
    db: Session,
    base_currency: str,
    quote_currency: str,
    target_date: date,
) -> FxRateObservation | None:
    return db.scalar(
        select(FxRateObservation)
        .where(
            FxRateObservation.base_currency == base_currency,
            FxRateObservation.quote_currency == quote_currency,
            FxRateObservation.as_of_date <= target_date,
        )
        .order_by(FxRateObservation.as_of_date.desc(), FxRateObservation.id.desc())
        .limit(1)
    )


def get_fx_conversion_rate(
    db: Session,
    base_currency: str,
    quote_currency: str,
    as_of_date: date,
    *,
    stale_after_days: int = 7,
) -> FxConversionRate:
    base = base_currency.strip().upper()
    quote = quote_currency.strip().upper()
    if base == quote:
        return FxConversionRate(
            base_currency=base,
            quote_currency=quote,
            rate=Decimal("1"),
            as_of_date=as_of_date,
            observation_id=None,
            provider_name="identity",
            inverted=False,
            age_days=0,
            is_stale=False,
        )

    direct = _latest_observation(db, base, quote, as_of_date)
    inverse = _latest_observation(db, quote, base, as_of_date)
    candidates = [
        (record.as_of_date, not is_direct, record)
        for is_direct, record in ((True, direct), (False, inverse))
        if record is not None
    ]
    if not candidates:
        raise FxRateUnavailable(base, quote, as_of_date)

    _, inverted, observation = max(candidates, key=lambda item: (item[0], not item[1], item[2].id))
    stored_rate = Decimal(observation.rate)
    if stored_rate <= 0:
        raise FxRateUnavailable(base, quote, as_of_date)
    rate = Decimal("1") / stored_rate if inverted else stored_rate
    age_days = (as_of_date - observation.as_of_date).days
    return FxConversionRate(
        base_currency=base,
        quote_currency=quote,
        rate=rate,
        as_of_date=observation.as_of_date,
        observation_id=observation.id,
        provider_name=observation.provider_name,
        inverted=inverted,
        age_days=age_days,
        is_stale=age_days > stale_after_days,
    )


def convert_amount(
    db: Session,
    amount: Decimal | float | int,
    base_currency: str,
    quote_currency: str,
    as_of_date: date,
    *,
    stale_after_days: int = 7,
) -> tuple[Decimal, FxConversionRate]:
    conversion = get_fx_conversion_rate(
        db,
        base_currency,
        quote_currency,
        as_of_date,
        stale_after_days=stale_after_days,
    )
    return Decimal(str(amount)) * conversion.rate, conversion
