import httpx
from app.providers.base import BaseSECProvider
from app.core.security import validate_safe_url

class SECProvider(BaseSECProvider):
    """Real implementation for fetching SEC EDGAR data."""
    
    def __init__(self, user_agent: str = "Market Intelligence App (contact@example.com)"):
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}
        
    def fetch_filing_text(self, url: str) -> str:
        validate_safe_url(url)
        response = httpx.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.text
        
    @property
    def provider_name(self) -> str:
        return "sec_edgar"
