from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import Company, FilingSection, RawDocument
from app.services.sec_parsing import parse_sec_filing
from app.services.sec_diff import _generate_html_diff, generate_section_diffs


def test_html_diff_escapes_untrusted_filing_text() -> None:
    diff_html, added_words, removed_words = _generate_html_diff(
        "Revenue was 100 <script>alert('old')</script>",
        'Revenue was 120 <img src=x onerror="alert(1)">',
    )

    assert added_words > 0
    assert removed_words > 0
    assert "<script>" not in diff_html
    assert "<img " not in diff_html
    assert "&lt;script&gt;" in diff_html
    assert "&lt;img " in diff_html


def test_new_section_diff_escapes_untrusted_filing_text(db_session) -> None:
    company = Company(ticker="SAFE", name="Safe Diff Co")
    db_session.add(company)
    db_session.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=1,
        document_type="sec_filing",
        title="Current 10-K",
        raw_text="Item 1. Business",
        content_hash="safe-diff-current",
    )
    db_session.add(document)
    db_session.flush()
    db_session.add(
        FilingSection(
            raw_document_id=document.id,
            item_name="Item 1",
            title="Business",
            text_content='<svg onload="alert(1)">',
            word_count=2,
        )
    )
    db_session.commit()

    [diff] = generate_section_diffs(db_session, document, None)

    assert "<svg " not in diff.diff_html
    assert "&lt;svg " in diff.diff_html

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


def test_parser_retry_repairs_partial_and_new_predecessor_without_replacing_sections(db, client):
    from sqlalchemy import select
    from app.models import Source, FilingSectionDiff
    company = Company(ticker="MOCKDIFF", name="Mock Data comparison retry")
    source = Source(name="Mock Data filing comparison", source_type="sec")
    db.add_all([company, source]); db.flush()
    def document(day):
        row = RawDocument(company_id=company.id, source_id=source.id, document_type="sec_filing_metadata",
            title=f"Mock Data filing {day}", raw_text=f"Item 1. Mock Data day {day} " + "business evidence " * 10,
            raw_payload_json={"form_type": "10-K"}, published_at=datetime(2026, 1, day, tzinfo=timezone.utc),
            content_hash=f"mock-comparison-{day}")
        db.add(row); db.commit()
        return row
    first, current = document(1), document(3)
    # Simulate the old post-section/pre-comparison failure boundary.
    sections = parse_sec_filing(db, current); db.commit()
    ids = [section.id for section in sections]
    assert client.get(f"/raw-documents/{current.id}/sections").json()["meta"]["is_stale"] is True
    assert client.post(f"/raw-documents/{current.id}/parse").status_code == 200
    diff = db.scalar(select(FilingSectionDiff))
    assert db.get(FilingSection, diff.prior_section_id).raw_document_id == first.id
    original_diff_id = diff.id
    intermediate = document(2)
    assert client.get(f"/raw-documents/{current.id}/sections").json()["meta"]["is_stale"] is True
    for _ in range(2):
        assert client.post(f"/raw-documents/{current.id}/parse").status_code == 200
    db.expire_all()
    diffs = list(db.scalars(select(FilingSectionDiff)))
    assert len(diffs) == 1 and diffs[0].id == original_diff_id
    assert db.get(FilingSection, diffs[0].prior_section_id).raw_document_id == intermediate.id
    assert [s.id for s in db.scalars(select(FilingSection).where(FilingSection.raw_document_id == current.id))] == ids
    assert client.get(f"/raw-documents/{current.id}/sections").json()["meta"]["is_stale"] is False
