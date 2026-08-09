from datetime import date
from decimal import Decimal

import pytest

from app.models import FxRateObservation
from app.services.fx_rates import FxRateUnavailable, convert_amount, get_fx_conversion_rate


def test_fx_lookup_uses_latest_point_on_or_before_date_and_preserves_source(db):
    db.add_all(
        [
            FxRateObservation(
                base_currency="INR",
                quote_currency="USD",
                rate=Decimal("0.0110"),
                as_of_date=date(2026, 8, 1),
                provider_name="manual",
            ),
            FxRateObservation(
                base_currency="INR",
                quote_currency="USD",
                rate=Decimal("0.0120"),
                as_of_date=date(2026, 8, 5),
                provider_name="manual",
            ),
        ]
    )
    db.commit()

    converted, source = convert_amount(db, 1000, "inr", "usd", date(2026, 8, 6))

    assert converted == Decimal("12.0000000000")
    assert source.as_of_date == date(2026, 8, 5)
    assert source.observation_id is not None
    assert source.age_days == 1
    assert source.is_stale is False


def test_fx_lookup_inverts_the_most_recent_inverse_pair(db):
    observation = FxRateObservation(
        base_currency="USD",
        quote_currency="EUR",
        rate=Decimal("0.8000"),
        as_of_date=date(2026, 8, 1),
        provider_name="manual",
    )
    db.add(observation)
    db.commit()

    result = get_fx_conversion_rate(db, "EUR", "USD", date(2026, 8, 10), stale_after_days=5)

    assert result.rate == Decimal("1.25")
    assert result.inverted is True
    assert result.is_stale is True


def test_fx_identity_and_missing_pair_are_explicit(db):
    identity = get_fx_conversion_rate(db, "USD", "USD", date(2026, 8, 1))
    assert identity.rate == 1
    assert identity.provider_name == "identity"

    with pytest.raises(FxRateUnavailable):
        get_fx_conversion_rate(db, "GBP", "USD", date(2026, 8, 1))
