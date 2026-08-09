from datetime import date

import pytest
from pydantic import ValidationError

from app.api.schemas import FxRateObservationCreate, PortfolioBenchmarkConfigCreate


def test_benchmark_contract_normalizes_symbols():
    payload = PortfolioBenchmarkConfigCreate(
        portfolio_id=1,
        ticker=" spy ",
        currency=" usd ",
        effective_from=date(2026, 1, 1),
    )

    assert payload.ticker == "SPY"
    assert payload.currency == "USD"


def test_fx_contract_normalizes_pair_and_requires_positive_rate():
    payload = FxRateObservationCreate(
        base_currency=" inr ",
        quote_currency=" usd ",
        rate=0.0119,
        as_of_date=date(2026, 1, 1),
    )

    assert (payload.base_currency, payload.quote_currency) == ("INR", "USD")

    with pytest.raises(ValidationError):
        FxRateObservationCreate(
            base_currency="USD",
            quote_currency="USD",
            rate=1,
            as_of_date=date(2026, 1, 1),
        )
    with pytest.raises(ValidationError):
        FxRateObservationCreate(
            base_currency="INR",
            quote_currency="USD",
            rate=0,
            as_of_date=date(2026, 1, 1),
        )
