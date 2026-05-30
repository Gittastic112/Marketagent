from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import Company, RawDocument
from app.services.sec_parsing import parse_sec_filing
from app.services.sec_diff import generate_section_diffs

def test_parse_sec_filing_and_diff():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    company = Company(ticker="TEST", name="Test Co")
    db.add(company)
    db.commit()
    
    prior_text = """
    <html>
        <body>
            <h1>10-K</h1>
            Item 1. Business
            We are a test company. We do testing.
            Item 1A. Risk Factors
            Testing is risky. We might fail.
            Item 2. Properties
            We own a computer. It is a very nice computer that is located in our main office headquarters which is very large indeed.
        </body>
    </html>
    """
    
    current_text = """
    <html>
        <body>
            <h1>10-K</h1>
            Item 1. Business
            We are a test company. We do testing and more testing.
            Item 1A. Risk Factors
            Testing is very risky. We might fail. We might crash.
            Item 2. Properties
            We own two computers. They are both extremely nice computers located in our large main office headquarters.
        </body>
    </html>
    """
    
    prior_doc = RawDocument(
        company_id=company.id,
        source_id=1,
        document_type="sec_filing",
        title="Prior 10-K",
        raw_text=prior_text,
        content_hash="hash1",
        published_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        raw_payload_json={"form_type": "10-K"}
    )
    current_doc = RawDocument(
        company_id=company.id,
        source_id=1,
        document_type="sec_filing",
        title="Current 10-K",
        raw_text=current_text,
        content_hash="hash2",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        raw_payload_json={"form_type": "10-K"}
    )
    db.add_all([prior_doc, current_doc])
    db.commit()
    
    # Test Parsing
    prior_sections = parse_sec_filing(db, prior_doc)
    db.commit()
    
    assert len(prior_sections) == 3
    assert prior_sections[0].item_name == "Item 1"
    assert "We are a test company" in prior_sections[0].text_content
    
    current_sections = parse_sec_filing(db, current_doc)
    db.commit()
    
    assert len(current_sections) == 3
    assert current_sections[1].item_name == "Item 1A"
    assert "Testing is very risky" in current_sections[1].text_content
    
    # Test Diffing
    diffs = generate_section_diffs(db, current_doc, prior_doc)
    db.commit()
    
    assert len(diffs) == 3
    assert diffs[0].added_words > 0
    assert diffs[1].added_words > 0
    assert diffs[2].added_words > 0
    
    # Check HTML diff output for Item 1A
    item_1a_diff = next(d for d in diffs if d.current_section.item_name == "Item 1A")
    assert "<ins class=\"diff-add\">very </ins>" in item_1a_diff.diff_html
    assert "We might crash." in item_1a_diff.diff_html
