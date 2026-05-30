import logging
from typing import Any
import httpx
from decimal import Decimal

from app.services.market_data.base import MarketDataProvider

logger = logging.getLogger(__name__)

class AlphaVantageProvider(MarketDataProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    async def get_quote(self, ticker: str) -> dict[str, Any] | None:
        if not self.api_key:
            logger.warning("Alpha Vantage API key not set.")
            return None

        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": self.api_key
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                quote = data.get("Global Quote", {})
                if not quote:
                    logger.warning(f"No global quote found for {ticker} in Alpha Vantage response.")
                    return None

                return {
                    "current_price": Decimal(quote.get("05. price", "0")),
                    "change_percent": Decimal(quote.get("10. change percent", "0").replace("%", "")),
                    "volume": int(quote.get("06. volume", "0")),
                }
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage quote for {ticker}: {e}")
            return None

    async def get_historical_prices(self, ticker: str, days: int = 365) -> list[dict[str, Any]]:
        if not self.api_key:
            logger.warning("Alpha Vantage API key not set.")
            return []

        # TIME_SERIES_DAILY requires outputsize=full for >100 days
        outputsize = "full" if days > 100 else "compact"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": outputsize,
            "apikey": self.api_key
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                time_series = data.get("Time Series (Daily)", {})
                if not time_series:
                    logger.warning(f"No time series found for {ticker} in Alpha Vantage response.")
                    return []

                results = []
                count = 0
                for date_str, daily_data in time_series.items():
                    if count >= days:
                        break
                    results.append({
                        "date": date_str,
                        "close_price": Decimal(daily_data.get("4. close", "0"))
                    })
                    count += 1
                return results
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage historical prices for {ticker}: {e}")
            return []
