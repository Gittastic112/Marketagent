from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class AIProviderResult:
    model_name: str
    output_text: str
    limitations: str
    confidence_label: str

class BaseAIProvider(ABC):
    """Base interface for all AI text generation providers."""
    
    @abstractmethod
    def generate_summary(self, text: str) -> AIProviderResult:
        """Generates a summary for the given text."""
        pass
        
    @abstractmethod
    def generate_chat_response(self, messages: list[dict], context: str = "") -> AIProviderResult:
        """Generates a chat response given a list of messages {"role": "user"|"assistant", "content": "..."}"""
        pass
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the name of the provider."""
        pass

class BaseSECProvider(ABC):
    """Base interface for SEC EDGAR interactions."""
    
    @abstractmethod
    def fetch_filing_text(self, url: str) -> str:
        pass
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

class BaseRSSProvider(ABC):
    """Base interface for RSS feed fetching."""
    
    @abstractmethod
    def fetch_feed_xml(self, url: str) -> str:
        pass
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

class BaseMacroProvider(ABC):
    """Base interface for fetching macroeconomic data."""
    
    @abstractmethod
    def fetch_series_info(self, series_id: str) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    def fetch_observations(self, series_id: str, limit: int = 100) -> list[Dict[str, Any]]:
        pass
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
