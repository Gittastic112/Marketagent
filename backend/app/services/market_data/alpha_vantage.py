import asyncio
import logging
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from app.providers.fixed_json import FixedJsonError, fetch_json

from app.services.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
    MarketDataRequest,
    MarketHistoryResult,
    MarketQuoteResult,
)
from app.services.market_data.sessions import history_window

logger = logging.getLogger(__name__)

class AlphaVantageProvider(MarketDataProvider):
    provider_name = "alpha_vantage"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    def _require_key(self) -> None:
        if not self.api_key:
            raise MarketDataProviderError(
                code="PROVIDER_NOT_CONFIGURED",
                message="Alpha Vantage is selected but its API key is not configured.",
                provider=self.provider_name,
                status_code=503,
                retryable=False,
            )

    def _raise_payload_error(self, data: dict, *, capability: str) -> None:
        if data.get("Note") or data.get("Information"):
            raise MarketDataProviderError(
                code="PROVIDER_RATE_LIMITED",
                message=f"Alpha Vantage did not provide {capability} because its request limit was reached.",
                provider=self.provider_name,
                status_code=429,
                retryable=True,
            )
        if data.get("Error Message"):
            raise MarketDataProviderError(
                code="PROVIDER_INVALID_SYMBOL",
                message=f"Alpha Vantage rejected the requested symbol for {capability}.",
                provider=self.provider_name,
                status_code=422,
                retryable=False,
            )

    def _currency(self, request: MarketDataRequest) -> tuple[str, list[str]]:
        if request.currency:
            return request.currency, ["Alpha Vantage did not supply currency; reviewed company currency was used."]
        inferred = "USD" if request.market == "US" else "INR" if request.market == "IN" else "UNKNOWN"
        return inferred, ["Provider currency was unavailable and inferred from market identity."]

    async def _get_json(self, params: dict[str, str], *, capability: str) -> dict:
        try:
            if self.base_url != "https://www.alphavantage.co/query":
                raise FixedJsonError("invalid_endpoint")
            data = await asyncio.to_thread(fetch_json, self.base_url, params, max_bytes=5_000_000, timeout=10)
            self._raise_payload_error(data, capability=capability)
            return data
        except MarketDataProviderError:
            raise
        except FixedJsonError as error:
            code, status = ("PROVIDER_RATE_LIMITED", 429) if error.status_code == 429 else (
                ("PROVIDER_TIMEOUT", 504) if error.kind == "timeout" else ("PROVIDER_UNAVAILABLE", 502))
            raise MarketDataProviderError(code=code, status_code=status, provider=self.provider_name,
                message=f"Alpha Vantage could not provide {capability} within its processing limits.") from None

    async def get_quote(self, request: MarketDataRequest) -> MarketQuoteResult:
        self._require_key()

        ticker = request.ticker
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": self.api_key
        }
        data = await self._get_json(params, capability="quote")
        quote = data.get("Global Quote", {})
        if not isinstance(quote, dict) or not quote:
            raise MarketDataProviderError(
                code="PROVIDER_EMPTY_RESPONSE",
                message="Alpha Vantage returned no quote for the requested symbol.",
                provider=self.provider_name,
                status_code=502,
                retryable=True,
            )

        try:
            current_price = Decimal(quote["05. price"])
            if current_price <= 0:
                raise ValueError("price must be positive")
            change_percent = Decimal(quote.get("10. change percent", "0").replace("%", ""))
            volume = int(quote.get("06. volume", "0"))
        except (KeyError, TypeError, ValueError, InvalidOperation):
            raise MarketDataProviderError(
                code="PROVIDER_INVALID_RESPONSE",
                message="Alpha Vantage returned an invalid quote payload.",
                provider=self.provider_name,
                status_code=502,
                retryable=False,
            ) from None

        currency, warnings = self._currency(request)
        warnings.append("Alpha Vantage did not supply a quote timestamp or delay classification.")
        return MarketQuoteResult(
            provider_name=self.provider_name,
            provider_symbol=ticker,
            market=request.market,
            exchange=request.exchange,
            ticker=request.ticker,
            current_price=current_price,
            change_percent=change_percent,
            volume=volume,
            currency=currency,
            observed_at=datetime.now(timezone.utc),
            price_type="unknown",
            adjustment_state="not_applicable",
            warnings=warnings,
        )

    async def get_historical_prices(
        self,
        request: MarketDataRequest,
        days: int = 365,
    ) -> list[MarketHistoryResult]:
        self._require_key()
        observed_at = datetime.now(timezone.utc)
        window = history_window(request, days, now=observed_at)

        ticker = request.ticker
        # TIME_SERIES_DAILY requires outputsize=full for >100 days
        outputsize = "full" if days > 100 else "compact"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": outputsize,
            "apikey": self.api_key
        }

        data = await self._get_json(params, capability="history")
        time_series = data.get("Time Series (Daily)", {})
        if not isinstance(time_series, dict) or not time_series:
            raise MarketDataProviderError(
                code="PROVIDER_EMPTY_RESPONSE",
                message="Alpha Vantage returned no price history for the requested symbol.",
                provider=self.provider_name,
                status_code=502,
                retryable=True,
            )

        currency, warnings = self._currency(request)
        results: list[MarketHistoryResult] = []
        warnings.append(window.warning)
        for date_str, daily_data in sorted(time_series.items()):
            try:
                day = date.fromisoformat(date_str)
                if not window.start <= day < window.end:
                    continue
                results.append(
                    MarketHistoryResult(
                        provider_name=self.provider_name,
                        provider_symbol=ticker,
                        market=request.market,
                        exchange=request.exchange,
                        ticker=request.ticker,
                        date=day,
                        close_price=Decimal(daily_data["4. close"]),
                        currency=currency,
                        observed_at=observed_at,
                        price_type="end_of_day",
                        adjustment_state="unadjusted",
                        warnings=warnings,
                    )
                )
            except (KeyError, TypeError, ValueError, InvalidOperation):
                logger.warning(
                    "Skipped invalid Alpha Vantage history row",
                    extra={"provider": self.provider_name},
                )

        if not results:
            raise MarketDataProviderError(
                code="PROVIDER_INVALID_RESPONSE",
                message="Alpha Vantage returned history without any valid price rows.",
                provider=self.provider_name,
                status_code=502,
                retryable=False,
            )
        return results
