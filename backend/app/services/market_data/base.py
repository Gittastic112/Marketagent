from abc import ABC, abstractmethod
from typing import Any

class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.
    """
    @abstractmethod
    async def get_quote(self, ticker: str) -> dict[str, Any] | None:
        """
        Fetch the latest market quote for a ticker.
        Returns a dictionary with at least:
        - current_price
        - change_percent
        - volume
        - fifty_two_week_high (optional)
        - fifty_two_week_low (optional)
        """
        pass

    @abstractmethod
    async def get_historical_prices(self, ticker: str, days: int = 365) -> list[dict[str, Any]]:
        """
        Fetch historical daily prices.
        Returns a list of dictionaries, each with:
        - date (YYYY-MM-DD)
        - close_price
        """
        pass
