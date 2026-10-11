from app.providers.base import BaseSECProvider
from app.providers.safe_http import fetch_public_text

class SECProvider(BaseSECProvider):
    """Real implementation for fetching SEC EDGAR data."""
    
    def __init__(self, user_agent: str = "Market Intelligence App (contact@example.com)"):
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}
        
    def fetch_filing_text(self, url: str) -> str:
        return fetch_public_text(url, headers=self.headers, max_bytes=40 * 1024 * 1024)
        
    @property
    def provider_name(self) -> str:
        return "sec_edgar"
