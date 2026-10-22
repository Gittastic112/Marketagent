from datetime import UTC, date, datetime, timedelta

from app.models import Company, FinancialExtractionCandidate, RawDocument, Source
from app.services.source_fact_history import list_source_facts_as_of, record_financial_fact_revision


def _candidate(db, *, company, document, value: float, suffix: str, claim_type: str | None = None):
    candidate = FinancialExtractionCandidate(
        company_id=company.id,
        raw_document_id=document.id,
        metric_code="revenue",
        reported_label="Revenue",
        value=value,
        unit="USD million",
        fiscal_year=2025,
        period_type="annual",
        source_text=f"Revenue {value}",
        source_locator_json={"claim_type": claim_type} if claim_type else None,
        extraction_method=f"point_in_time_test_{suffix}",
        confidence_label="high",
        review_status="reviewed",
    )
    db.add(candidate)
    db.flush()
    return candidate


def test_source_fact_history_returns_revision_visible_at_cutoff(db):
    company = Company(ticker="PIT", name="Point in Time", market="US")
    source = Source(name="Point in time source", source_type="filing")
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="2025 annual report",
        raw_text="Revenue 100\nRevenue 110",
        content_hash="point-in-time-history",
    )
    db.add(document)
    db.flush()

    first = record_financial_fact_revision(
        db,
        _candidate(db, company=company, document=document, value=100, suffix="first"),
        effective_at=date(2025, 12, 31),
    )
    db.flush()
    first.observed_at = datetime.now(UTC) - timedelta(days=1)
    cutoff = datetime.now(UTC) - timedelta(hours=12)
    second = record_financial_fact_revision(
        db,
        _candidate(db, company=company, document=document, value=110, suffix="second"),
        effective_at=date(2025, 12, 31),
    )
    db.commit()

    historical = list_source_facts_as_of(db, company.id, as_of=cutoff)
    current = list_source_facts_as_of(db, company.id)

    assert historical[0].id == first.id
    assert historical[0].value == 100
    assert current[0].id == second.id
    assert current[0].revision_number == 2
    assert second.claim_type == "Fact"


def test_source_fact_history_preserves_calculation_claim_type(db):
    company = Company(ticker="CALC", name="Calculated Fact", market="IN")
    source = Source(name="Audited filing", source_type="filing")
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2025 annual report",
        raw_text="Revenue less operating expenses equals EBIT",
        content_hash="calculated-source-fact",
    )
    db.add(document)
    db.flush()

    revision = record_financial_fact_revision(
        db,
        _candidate(
            db,
            company=company,
            document=document,
            value=140,
            suffix="ebit",
            claim_type="Calculation",
        ),
        effective_at=date(2025, 3, 31),
    )
    db.commit()

    assert revision.claim_type == "Calculation"


def test_restatement_supersedes_all_legacy_active_occurrences_without_deleting_history(db):
    company = Company(ticker="DUPREV", name="Mock Data legacy revisions", market="US")
    source = Source(name="Mock Data revision source", source_type="filing")
    db.add_all([company, source])
    db.flush()
    document = RawDocument(company_id=company.id, source_id=source.id,
        document_type="annual_report", title="Mock Data source occurrences",
        raw_text="Revenue 100\nRevenue 100\nRevenue 110", content_hash="legacy-active-revisions")
    db.add(document)
    db.flush()
    effective_at = date(2025, 12, 31)
    first = record_financial_fact_revision(db,
        _candidate(db, company=company, document=document, value=100, suffix="first"),
        effective_at=effective_at)
    db.flush()
    second = record_financial_fact_revision(db,
        _candidate(db, company=company, document=document, value=100, suffix="repeat"),
        effective_at=effective_at)
    db.flush()
    # Earlier intake could leave both identical source occurrences active.
    first.superseded_at = None
    db.flush()
    current = record_financial_fact_revision(db,
        _candidate(db, company=company, document=document, value=110, suffix="revised"),
        effective_at=effective_at)
    db.flush()
    assert first.superseded_at == second.superseded_at == current.observed_at
    assert first.value == second.value == 100
    assert current.value == 110 and current.revision_number == 3
    assert current.superseded_at is None
