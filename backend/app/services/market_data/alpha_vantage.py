import logging
from datetime import datetime, timezone
from decimal import Decimal

import httpx

from app.services.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
    MarketDataRequest,
    MarketHistoryResult,
    MarketQuoteResult,
)

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
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
            if response.status_code == 429:
                raise MarketDataProviderError(
                    code="PROVIDER_RATE_LIMITED",
                    message=f"Alpha Vantage rate-limited the {capability} request.",
                    provider=self.provider_name,
                    status_code=429,
                    retryable=True,
                )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Provider response was not an object")
            self._raise_payload_error(data, capability=capability)
            return data
        except MarketDataProviderError:
            raise
        except httpx.TimeoutException as exc:
            raise MarketDataProviderError(
                code="PROVIDER_TIMEOUT",
                message=f"Alpha Vantage timed out while fetching {capability}.",
                provider=self.provider_name,
                status_code=504,
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise MarketDataProviderError(
                code="PROVIDER_UNAVAILABLE",
                message=f"Alpha Vantage could not provide {capability}.",
                provider=self.provider_name,
                status_code=502,
                retryable=True,
            ) from exc
        except (TypeError, ValueError) as exc:
            raise MarketDataProviderError(
                code="PROVIDER_INVALID_RESPONSE",
                message=f"Alpha Vantage returned invalid {capability} data.",
                provider=self.provider_name,
                status_code=502,
                retryable=False,
            ) from exc

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
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketDataProviderError(
                code="PROVIDER_INVALID_RESPONSE",
                message="Alpha Vantage returned an invalid quote payload.",
                provider=self.provider_name,
                status_code=502,
                retryable=False,
            ) from exc

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
        observed_at = datetime.now(timezone.utc)
        results: list[MarketHistoryResult] = []
        for date_str, daily_data in list(time_series.items())[:days]:
            try:
                results.append(
                    MarketHistoryResult(
                        provider_name=self.provider_name,
                        provider_symbol=ticker,
                        market=request.market,
                        exchange=request.exchange,
                        ticker=request.ticker,
                        date=date_str,
                        close_price=Decimal(daily_data["4. close"]),
                        currency=currency,
                        observed_at=observed_at,
                        price_type="end_of_day",
                        adjustment_state="unadjusted",
                        warnings=warnings,
                    )
                )
            except (KeyError, TypeError, ValueError):
                logger.warning(
                    "Skipped invalid Alpha Vantage history row",
                    extra={"provider": self.provider_name, "ticker": ticker, "date": date_str},
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
