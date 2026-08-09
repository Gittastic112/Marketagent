import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import DamodaranCapexBenchmark
from app.models.real_options import IndustryVolatilityBenchmark
from app.services.damodaran_coverage import (
    DAMODARAN_APPLICATION_COVERAGE,
    build_damodaran_coverage_report,
)
from helpers import response_data


def _row(report: dict, filename: str) -> dict:
    return next(item for item in report["rows"] if item["source_filename"] == filename)


def test_coverage_registry_is_complete_and_preserves_source_boundaries() -> None:
    assert len(DAMODARAN_APPLICATION_COVERAGE) == 35
    assert len({spec.source_filename for spec in DAMODARAN_APPLICATION_COVERAGE}) == 35
    assert len({spec.canonical_path for spec in DAMODARAN_APPLICATION_COVERAGE}) == 35

    rating = next(
        spec for spec in DAMODARAN_APPLICATION_COVERAGE
        if spec.source_filename == "ratings.xls"
    )
    assert rating.source_as_of == "unknown"
    assert rating.date_confidence == "low"
    assert rating.implementation_status == "supported"
    assert rating.supported_metrics == (
        "large non-financial rating bounds",
        "small or risky firm rating bounds",
        "financial-service rating bounds",
        "default spreads",
        "versioned source provenance",
        "interest-coverage rating calculation service",
    )
    assert rating.missing_metrics == ("operating-lease capitalization",)

    roe = next(
        spec for spec in DAMODARAN_APPLICATION_COVERAGE
        if spec.source_filename == "roeIndia.xls"
    )
    assert roe.implementation_status == "supported"
    assert roe.ingestion_available is True
    assert roe.supported_metrics == (
        "firm count",
        "unadjusted ROE",
        "R&D-adjusted ROE",
        "versioned source provenance",
    )
    assert roe.missing_metrics == ()

    volatility = next(
        spec for spec in DAMODARAN_APPLICATION_COVERAGE
        if spec.source_filename == "optvarIndia.xls"
    )
    assert volatility.implementation_status == "supported"
    assert volatility.ingestion_available is True
    assert volatility.supported_metrics == (
        "firm count",
        "equity volatility",
        "firm-value volatility",
        "equity weight",
        "debt weight",
        "debt-to-equity volatility ratio assumption",
        "stock-bond correlation assumption",
        "versioned source provenance",
    )

    pricing = {
        spec.source_filename: spec
        for spec in DAMODARAN_APPLICATION_COVERAGE
        if spec.source_filename in {"peIndia.xls", "pbvIndia.xls", "psIndia.xls", "vebitdaIndia.xls"}
    }
    assert set(pricing) == {"peIndia.xls", "pbvIndia.xls", "psIndia.xls", "vebitdaIndia.xls"}
    assert all(spec.implementation_status == "supported" for spec in pricing.values())
    assert all(spec.missing_metrics == () for spec in pricing.values())
    assert all("versioned source provenance" in spec.supported_metrics for spec in pricing.values())

    historical = {
        spec.source_filename: spec.catalog_status
        for spec in DAMODARAN_APPLICATION_COVERAGE
        if spec.source_filename in {"macro.xls", "macrodur.xls"}
    }
    assert historical == {
        "macro.xls": "historical_only",
        "macrodur.xls": "historical_only",
    }
    geographies = {
        spec.source_filename: spec.geography
        for spec in DAMODARAN_APPLICATION_COVERAGE
        if spec.source_filename in {
            "countrystats.xls",
            "countrytaxrates.xls",
            "insholdGlobal.xls",
        }
    }
    assert geographies == {
        "countrystats.xls": "Global",
        "countrytaxrates.xls": "Global",
        "insholdGlobal.xls": "Global",
    }
    country_stats = next(
        spec
        for spec in DAMODARAN_APPLICATION_COVERAGE
        if spec.source_filename == "countrystats.xls"
    )
    assert country_stats.implementation_status == "supported"
    assert country_stats.missing_metrics == ()
    assert "versioned source provenance" in country_stats.supported_metrics
    assert "total dividends" in country_stats.supported_metrics


def test_coverage_report_distinguishes_typed_rows_from_metadata_only(
    db_session: Session,
    tmp_path: Path,
) -> None:
    for filename in ("capexIndia.xls", "betaIndia.xls", "ratings.xls", "roeIndia.xls"):
        (tmp_path / filename).write_bytes(b"fixture")

    capex_file = DamodaranDatasetFile(
        uploaded_filename="capexIndia.xls",
        dataset_code="capex",
        country="India",
        source_file_type="xls",
        source_sha256=hashlib.sha256(b"fixture").hexdigest(),
        source_as_of="2026-01-05",
        date_confidence="high",
        canonical_source_path="raw/datasets/capexIndia.xls",
        import_kind="typed",
        is_active=True,
        row_count=1,
    )
    beta_file = DamodaranDatasetFile(
        uploaded_filename="betaIndia.xls",
        dataset_code="beta",
        country="India",
        source_file_type="xls",
    )
    db_session.add_all([capex_file, beta_file])
    db_session.flush()
    db_session.add(
        DamodaranCapexBenchmark(
            dataset_file_id=capex_file.id,
            industry_name="Transportation",
            country="India",
            capex_to_sales=0.12,
            net_capex_to_sales=0.08,
            sales_to_capital=1.5,
        )
    )
    db_session.commit()

    report = build_damodaran_coverage_report(
        db_session,
        data_root=tmp_path,
    )

    assert report["source_count"] == 35
    assert report["source_present_count"] == 4
    assert report["typed_record_count"] == 1
    assert report["provenance_complete_count"] == 1

    capex = _row(report, "capexIndia.xls")
    assert capex["implementation_status"] == "partial"
    assert capex["ingestion_status"] == "ingested"
    assert capex["typed_record_count"] == 1
    assert capex["freshness_status"] == "current"
    assert capex["stored_version_count"] == 1
    assert capex["active_version_id"] == capex_file.id
    assert capex["active_source_sha256"] == hashlib.sha256(b"fixture").hexdigest()
    assert capex["active_source_as_of"] == "2026-01-05"
    assert capex["active_date_confidence"] == "high"
    assert capex["active_import_kind"] == "typed"
    assert capex["provenance_status"] == "complete"

    beta = _row(report, "betaIndia.xls")
    assert beta["implementation_status"] == "unsupported"
    assert beta["ingestion_status"] == "metadata_only"
    assert beta["typed_record_count"] == 0
    assert beta["provenance_status"] == "missing"

    rating = _row(report, "ratings.xls")
    assert rating["ingestion_status"] == "not_ingested"
    assert rating["freshness_status"] == "user_assumed_recent"
    assert rating["source_as_of"] == "unknown"

    roe = _row(report, "roeIndia.xls")
    assert roe["implementation_status"] == "supported"
    assert roe["ingestion_status"] == "not_ingested"

    missing = _row(report, "marginIndia.xls")
    assert missing["source_present"] is False
    assert missing["ingestion_status"] == "source_missing"


def test_damodaran_coverage_endpoint_returns_typed_honest_inventory(client) -> None:
    report = response_data(client.get("/data-health/damodaran-coverage"))

    assert report["inventory_version"] == "2026-08-08.6"
    assert report["source_count"] == 35
    assert report["supported_count"] + report["partial_count"] + report["unsupported_count"] == 35
    assert report["typed_record_count"] >= 0
    assert report["provenance_complete_count"] >= 0
    assert report["generated_at"]
    assert report["limitations"]
    assert len(report["rows"]) == 35

    rating = _row(report, "ratings.xls")
    assert rating["claim_type"] == "Source Summary"
    assert rating["freshness_status"] == "user_assumed_recent"

    response = client.get("/data-health/damodaran-coverage")
    assert response.json()["meta"]["source"] == "damodaran_application_coverage"
    assert response.json()["meta"]["is_mock"] is False


def test_coverage_counts_only_active_versioned_volatility_rows(
    db_session: Session,
    tmp_path: Path,
) -> None:
    source_bytes = b"active-volatility-source"
    (tmp_path / "optvarIndia.xls").write_bytes(source_bytes)
    old = DamodaranDatasetFile(
        uploaded_filename="optvarIndia.xls",
        dataset_code="volatility",
        country="India",
        source_file_type="xls",
        source_sha256="old-hash",
        source_as_of="2026-01-05",
        date_confidence="high",
        canonical_source_path="raw/datasets/optvarIndia(1).xls",
        import_kind="typed",
        is_active=False,
        row_count=1,
    )
    active = DamodaranDatasetFile(
        uploaded_filename="optvarIndia.xls",
        dataset_code="volatility",
        country="India",
        source_file_type="xls",
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        source_as_of="2026-01-05",
        date_confidence="high",
        canonical_source_path="raw/datasets/optvarIndia(1).xls",
        import_kind="typed",
        is_active=True,
        row_count=1,
    )
    db_session.add_all([old, active])
    db_session.flush()
    db_session.add_all(
        [
            IndustryVolatilityBenchmark(
                dataset_file_id=old.id,
                country="India",
                industry_name="Advertising",
                source_file="optvarIndia.xls",
            ),
            IndustryVolatilityBenchmark(
                dataset_file_id=active.id,
                country="India",
                industry_name="Advertising",
                source_file="optvarIndia.xls",
            ),
            IndustryVolatilityBenchmark(
                dataset_file_id=None,
                country="India",
                industry_name="Legacy Unproven",
                source_file="optvarIndia.xls",
            ),
        ]
    )
    db_session.commit()

    report = build_damodaran_coverage_report(db_session, data_root=tmp_path)
    row = _row(report, "optvarIndia.xls")

    assert row["typed_record_count"] == 1
    assert row["active_version_id"] == active.id
    assert row["provenance_status"] == "complete"
    assert row["hash_matches_mirror"] is True
