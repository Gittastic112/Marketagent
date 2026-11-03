from datetime import datetime, timezone
from decimal import Decimal

import yfinance as yf

from app.services.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
    MarketDataRequest,
    MarketHistoryResult,
    MarketQuoteResult,
)
from app.services.market_data.sessions import history_window
from app.services.market_data.yfinance_jobs import run_yfinance_job


class YFinanceMarketProvider(MarketDataProvider):
    provider_name = "yfinance_personal"
    _warning = "yfinance is an unofficial personal-use source; verify material prices against an official source."

    def provider_symbol(self, request: MarketDataRequest) -> str:
        ticker = request.ticker.upper()
        if request.market == "IN" and not ticker.endswith((".NS", ".BO")):
            suffix = ".BO" if request.exchange == "BSE" else ".NS"
            return f"{ticker}{suffix}"
        return ticker

    def _fetch_quote(self, request: MarketDataRequest) -> MarketQuoteResult:
        provider_symbol = self.provider_symbol(request)
        try:
            ticker_obj = yf.Ticker(provider_symbol)
            info = ticker_obj.fast_info
            last_price = info.get("lastPrice")
            if last_price is None or last_price <= 0:
                hist = ticker_obj.history(period="1d", auto_adjust=False)
                if not hist.empty:
                    last_price = hist["Close"].iloc[-1]
            if last_price is None or last_price <= 0:
                raise ValueError("price was missing or non-positive")

            currency = info.get("currency") or request.currency
            if not currency:
                raise ValueError("currency was missing")
            observed_at = datetime.now(timezone.utc)
            return MarketQuoteResult(
                provider_name=self.provider_name,
                provider_symbol=provider_symbol,
                market=request.market,
                exchange=request.exchange,
                ticker=request.ticker,
                currency=currency,
                current_price=Decimal(str(last_price)),
                observed_at=observed_at,
                price_type="unknown",
                adjustment_state="not_applicable",
                warnings=[self._warning, "Quote timestamp and delay classification were not supplied."],
            )
        except Exception:
            raise MarketDataProviderError(
                code="PROVIDER_UNAVAILABLE",
                message="yfinance could not return a usable market quote.",
                provider=self.provider_name,
                status_code=502,
                retryable=True,
            ) from None

    async def get_quote(self, request: MarketDataRequest) -> MarketQuoteResult:
        return await run_yfinance_job("quote", request)

    def _fetch_history(self, request: MarketDataRequest, days: int) -> list[MarketHistoryResult]:
        provider_symbol = self.provider_symbol(request)
        try:
            ticker_obj = yf.Ticker(provider_symbol)
            window = history_window(request, days, now=datetime.now(timezone.utc))
            history = ticker_obj.history(
                start=window.start.isoformat(), end=window.end.isoformat(), auto_adjust=False,
            )
            if history.empty:
                raise ValueError("history was empty")
            currency = ticker_obj.fast_info.get("currency") or request.currency
            if not currency:
                raise ValueError("currency was missing")
            observed_at = datetime.now(timezone.utc)
            results = [
                MarketHistoryResult(
                    provider_name=self.provider_name,
                    provider_symbol=provider_symbol,
                    market=request.market,
                    exchange=request.exchange,
                    ticker=request.ticker,
                    currency=currency,
                    date=index.date(),
                    close_price=Decimal(str(row["Close"])),
                    observed_at=observed_at,
                    price_type="end_of_day",
                    adjustment_state="unadjusted",
                    warnings=[
                        self._warning,
                        window.warning,
                    ],
                )
                for index, row in history.iterrows()
                if window.start <= index.date() < window.end and row.get("Close") is not None and row["Close"] > 0
            ]
            if not results:
                raise ValueError("history contained no positive closing prices")
            return results
        except MarketDataProviderError:
            raise
        except Exception:
            raise MarketDataProviderError(
                code="PROVIDER_UNAVAILABLE",
                message="yfinance could not return usable market-price history.",
                provider=self.provider_name,
                status_code=502,
                retryable=True,
            ) from None

    async def get_historical_prices(
        self,
        request: MarketDataRequest,
        days: int = 365,
    ) -> list[MarketHistoryResult]:
        return await run_yfinance_job("history", request, days)
