from pathlib import Path

import pytest

from app.models import ProcessingRun
from app.models.assumption_methodology import AssumptionMethodValue
from app.models.damodaran import DamodaranDatasetFile
from app.services.assumption_methodology import AssumptionMethodologyService
from app.services.damodaran_ingestion import DamodaranBenchmarkIngestionService as Importer
from app.services.damodaran_us_ingestion import ingest_us_benchmarks
from app.services.industry_mapping import IndustryMappingService

DATA = Path(__file__).resolve().parents[2] / "data" / "damodaran" / "raw"


def test_us_sources_are_dated_audited_idempotent_and_country_separated(db_session):
    Importer.ingest_beta_methods_file(db_session, str(DATA / "betaIndia.xls"), "India")
    india = db_session.query(DamodaranDatasetFile).one()
    counts = ingest_us_benchmarks(db_session, DATA)
    assert counts == {"beta_methods": 282, "wacc_methods": 473,
        "margin": 94, "capex": 94, "roe": 94, "working_capital": 94}
    assert ingest_us_benchmarks(db_session, DATA) == counts
    versions = db_session.query(DamodaranDatasetFile).filter_by(country="United States").all()
    assert len(versions) == 6
    assert all(row.is_active and row.source_as_of == "2026-01-05" and row.source_sha256 and row.canonical_source_path for row in versions)
    db_session.refresh(india)
    assert india.is_active
    methods = db_session.query(AssumptionMethodValue).filter_by(country="United States").all()
    assert all(row.currency != "INR" for row in methods)
    erp = AssumptionMethodologyService.get_default_method(db_session, "equity_risk_premium", "US", currency="USD")
    assert erp["value"] == pytest.approx(0.0446)
    assert erp["source"]["source_row"] == "10"
    assert erp["requires_review"] is True
    beta = AssumptionMethodologyService.get_default_method(db_session, "beta", "United States", "Advertising")
    assert beta["value"] == pytest.approx(1.210506967409714)
    industries = IndustryMappingService.get_available_industries(db_session, "United States", fallback_to_loaded=False)
    assert len(industries) == 94
    assert "Semiconductor" in industries
    runs = db_session.query(ProcessingRun).order_by(ProcessingRun.id).all()
    assert len(runs) == 12 and all(run.status == "success" for run in runs)
    assert sum(run.created_count for run in runs) == sum(counts.values())
    assert sum(run.skipped_duplicate_count for run in runs) == sum(counts.values())


@pytest.mark.parametrize("wrong_field", ["scope", "date"])
def test_us_import_rejects_mislabeled_or_redated_sources(db_session, monkeypatch, wrong_field):
    raw = Importer._read_industry_averages(DATA / "waccUS-2026-01-05.xls")
    if wrong_field == "scope":
        raw.iloc[2, 5] = "India"
    else:
        raw.iloc[0, 1] = "2025-01-05"
    monkeypatch.setattr(Importer, "_read_industry_averages", staticmethod(lambda path: raw))
    with pytest.raises(ValueError):
        ingest_us_benchmarks(db_session, DATA, {"wacc_methods"})
    assert db_session.query(AssumptionMethodValue).count() == 0
    assert db_session.query(DamodaranDatasetFile).count() == 0
    assert db_session.query(ProcessingRun).one().status == "failed"
