from app.providers.base import BaseRSSProvider
from app.providers.safe_http import fetch_public_text

class RSSProvider(BaseRSSProvider):
    """Real implementation for fetching RSS feeds."""
    
    def fetch_feed_xml(self, url: str) -> str:
        return fetch_public_text(url, max_bytes=4 * 1024 * 1024)
        
    @property
    def provider_name(self) -> str:
        return "rss_http"
