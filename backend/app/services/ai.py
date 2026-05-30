import hashlib
import logging
import os

from sqlalchemy.orm import Session
from app.models import AiOutput, RawDocument
from app.providers.ai_provider import GeminiAIProvider
from app.providers.mock_provider import MockAIProvider

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1.0.0-summary"

def _hash_input(text: str) -> str:
    """Creates an MD5 hash of the input text for tracking provenance."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def generate_document_summary(db: Session, document: RawDocument) -> AiOutput:
    """
    Generates an AI summary for a RawDocument using the Provider Adapter Layer.
    """
    text_to_summarize = document.raw_text or document.title
    input_hash = _hash_input(text_to_summarize)
    
    api_key = os.environ.get("GEMINI_API_KEY")
    is_test = os.environ.get("PYTEST_CURRENT_TEST") is not None
    
    if api_key and not is_test:
        logger.info("Using real AI provider for summary generation.")
        provider = GeminiAIProvider(api_key=api_key)
    else:
        logger.info("Using mocked AI response.")
        provider = MockAIProvider()
        
    try:
        result = provider.generate_summary(text_to_summarize)
    except Exception as e:
        logger.error(f"Provider failed, falling back to mock: {e}")
        provider = MockAIProvider()
        result = provider.generate_summary(text_to_summarize)
        
    ai_output = AiOutput(
        raw_document_id=document.id,
        model_name=result.model_name,
        prompt_version=PROMPT_VERSION,
        input_hash=input_hash,
        output_text=result.output_text,
        limitations=result.limitations,
        confidence_label=result.confidence_label,
        human_review_status="pending"
    )
    
    db.add(ai_output)
    db.commit()
    db.refresh(ai_output)
    
    return ai_output
