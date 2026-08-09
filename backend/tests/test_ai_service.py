import os
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import Company, RawDocument
from app.services.ai import generate_document_summary

def test_generate_document_summary_mocked():
    # Set PYTEST_CURRENT_TEST to ensure the mock is used even if an API key is present
    os.environ["PYTEST_CURRENT_TEST"] = "test_generate_document_summary_mocked"

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()

    company = Company(ticker="TEST", name="Test Co")
    db.add(company)
    db.commit()

    doc = RawDocument(
        company_id=company.id,
        source_id=1,
        document_type="sec_filing",
        title="Test Document",
        raw_text="This is a test document that should be summarized by the AI.",
        content_hash="aihash1",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        raw_payload_json={"form_type": "10-K"}
    )
    db.add(doc)
    db.commit()

    ai_output = generate_document_summary(
        db,
        doc,
        user_id="admin_user_id_fallback",
    )
    db.commit()

    assert ai_output.raw_document_id == doc.id
    assert ai_output.model_name == "mock-model"
    assert "Mock Data: AI Summary" in ai_output.output_text
    assert ai_output.provider_name == "mock"
    assert ai_output.is_mock is True
    assert ai_output.transmission_scope == "none"
    assert ai_output.source_ids_json == [f"raw_document:{doc.id}", "source:1"]
    assert ai_output.human_review_status == "pending"
    assert "High" in ai_output.confidence_label
