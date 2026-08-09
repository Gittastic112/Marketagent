from sqlalchemy.orm import Session

from app.models import AiOutput, RawDocument
from app.services.ai_contract import AIProvenance, execute_ai_generation


PROMPT_VERSION = "v1.1.0-summary-contract"


def generate_document_summary(
    db: Session,
    document: RawDocument,
    *,
    user_id: str,
) -> AiOutput:
    text_to_summarize = document.raw_text or document.title
    source_ids = [f"raw_document:{document.id}"]
    if document.source_id:
        source_ids.append(f"source:{document.source_id}")

    return execute_ai_generation(
        db,
        provenance=AIProvenance(
            user_id=user_id,
            raw_document_id=document.id,
            reference_type="raw_document",
            reference_id=document.id,
            prompt_version=PROMPT_VERSION,
            input_text=text_to_summarize,
            source_ids=tuple(source_ids),
            source_scope="raw_document_text",
            external_data_classes=("raw_document_text",),
        ),
        generate=lambda provider: provider.generate_summary(text_to_summarize),
    )
