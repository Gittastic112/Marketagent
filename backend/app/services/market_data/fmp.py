import logging
from typing import Any

from app.services.market_data.base import MarketDataProvider

logger = logging.getLogger(__name__)

class FMPProvider(MarketDataProvider):
    """
    Placeholder for Financial Modeling Prep (FMP) integration.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_quote(self, ticker: str) -> dict[str, Any] | None:
        logger.warning("FMPProvider get_quote is not yet implemented.")
        return None

    async def get_historical_prices(self, ticker: str, days: int = 365) -> list[dict[str, Any]]:
        logger.warning("FMPProvider get_historical_prices is not yet implemented.")
        return []
