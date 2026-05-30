import httpx
from app.providers.base import BaseRSSProvider
from app.core.security import validate_safe_url

class RSSProvider(BaseRSSProvider):
    """Real implementation for fetching RSS feeds."""
    
    def fetch_feed_xml(self, url: str) -> str:
        validate_safe_url(url)
        response = httpx.get(url, timeout=20)
        response.raise_for_status()
        return response.text
        
    @property
    def provider_name(self) -> str:
        return "rss_http"
