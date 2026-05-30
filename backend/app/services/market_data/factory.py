from app.core.config import get_settings
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.alpha_vantage import AlphaVantageProvider
from app.services.market_data.fmp import FMPProvider

def get_market_data_provider() -> MarketDataProvider:
    """
    Factory function to get the configured market data provider.
    """
    settings = get_settings()
    
    if settings.market_data_provider == "fmp":
        return FMPProvider(api_key=settings.fmp_api_key or "")
    
    # Default to alpha vantage
    return AlphaVantageProvider(api_key=settings.alpha_vantage_api_key or "")
