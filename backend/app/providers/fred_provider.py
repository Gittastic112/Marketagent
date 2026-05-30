from typing import Any, Dict, List
import urllib.request
import urllib.parse
import json
import logging

from app.providers.base import BaseMacroProvider

logger = logging.getLogger(__name__)

class FredProvider(BaseMacroProvider):
    """
    Provider for Federal Reserve Economic Data (FRED).
    Requires a FRED API key.
    """
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        
    @property
    def provider_name(self) -> str:
        return "FRED"
        
    def fetch_series_info(self, series_id: str) -> Dict[str, Any]:
        """Fetch metadata about a specific FRED series."""
        if not self.api_key:
            raise ValueError("FRED API key is required to fetch series data.")
            
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json"
        }
        url = f"{self.base_url}/series?{urllib.parse.urlencode(params)}"
        
        request = urllib.request.Request(url, headers={"User-Agent": "Market Intelligence Engine"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "seriess" not in data or len(data["seriess"]) == 0:
                    raise ValueError(f"Series {series_id} not found in FRED.")
                return data["seriess"][0]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"FRED API error fetching series info: {e.status} {e.reason}")
            
    def fetch_observations(self, series_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch the latest observations for a given FRED series."""
        if not self.api_key:
            raise ValueError("FRED API key is required to fetch observations.")
            
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        url = f"{self.base_url}/series/observations?{urllib.parse.urlencode(params)}"
        
        request = urllib.request.Request(url, headers={"User-Agent": "Market Intelligence Engine"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "observations" not in data:
                    return []
                return data["observations"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"FRED API error fetching observations: {e.status} {e.reason}")
