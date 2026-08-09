import hashlib
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import DamodaranPricingBenchmark
from app.services.damodaran_ingestion import DamodaranBenchmarkIngestionService


APPROVED_HASHES = {
    "peIndia.xls": "e363c3fefb9bc3d225239d5823c18b09586bd91264151c3442d380bbcbbc21f4",
    "pbvIndia.xls": "1944f8604552632a2e2470ba36f109e7e3d2ecc7e6d9da2aaf5793c7b004d615",
    "psIndia.xls": "dc40093f51f0f203dc2bf1c6e7e152899249829351c3cf76e750d253a9f152f4",
    "vebitdaIndia.xls": "75edc529c84fabb3356411c04e77f16b281d5574764c7adf497421788ccf334f",
}


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def _approved_source(filename: str) -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "damodaran" / "raw" / filename


@pytest.mark.parametrize(
    ("filename", "dataset_code", "importer"),
    [
        ("peIndia.xls", "pe", "ingest_pe_file"),
        ("pbvIndia.xls", "pbv", "ingest_pbv_file"),
        ("psIndia.xls", "ps", "ingest_ps_file"),
        ("vebitdaIndia.xls", "vebitda", "ingest_vebitda_file"),
    ],
)
def test_pricing_sources_are_exact_versioned_and_idempotent(
    filename: str,
    dataset_code: str,
    importer: str,
) -> None:
    db = _session()
    try:
        source = _approved_source(filename)
        ingest = getattr(DamodaranBenchmarkIngestionService, importer)
        assert ingest(db, str(source), "India") == 94
        assert ingest(db, str(source), "India") == 94

        version = db.query(DamodaranDatasetFile).one()
        assert version.dataset_code == dataset_code
        assert version.source_sha256 == APPROVED_HASHES[filename]
        assert version.source_as_of == "2026-01-05"
        assert version.date_confidence == "high"
        assert version.import_kind == "typed"
        assert version.is_active is True
        assert version.row_count == 94
        assert db.query(DamodaranPricingBenchmark).count() == 94
        assert db.query(DamodaranPricingBenchmark).filter(
            DamodaranPricingBenchmark.industry_name.like("Total Market%")
        ).count() == 0
    finally:
        db.close()


def test_pricing_sources_preserve_exact_interpretation_controls() -> None:
    db = _session()
    try:
        for filename, importer in (
            ("peIndia.xls", "ingest_pe_file"),
            ("pbvIndia.xls", "ingest_pbv_file"),
            ("psIndia.xls", "ingest_ps_file"),
            ("vebitdaIndia.xls", "ingest_vebitda_file"),
        ):
            getattr(DamodaranBenchmarkIngestionService, importer)(
                db, str(_approved_source(filename)), "India"
            )

        rows = {
            dataset.dataset_code: row
            for row, dataset in db.query(DamodaranPricingBenchmark, DamodaranDatasetFile)
            .join(DamodaranDatasetFile, DamodaranDatasetFile.id == DamodaranPricingBenchmark.dataset_file_id)
            .filter(DamodaranPricingBenchmark.industry_name == "Advertising")
            .all()
        }
        pe = rows["pe"]
        assert pe.number_of_firms == 24
        assert pe.pe_current == 43.47618468388624
        assert pe.pe_aggregate_all_firms == 39.328570176207585
        assert pe.pe_aggregate_money_making == 25.763663096490372
        assert pe.expected_growth_next_five_years == 0.293
        assert pe.peg_ratio == 0.8793059077300469

        pbv = rows["pbv"]
        assert pbv.number_of_firms == 24
        assert pbv.pbv_ratio == 2.6275250528584557
        assert pbv.roe == 0.07969239127453762
        assert pbv.ev_to_invested_capital == 2.906771489117338
        assert pbv.roic == 0.14820964828899713

        ps = rows["ps"]
        assert ps.number_of_firms == 24
        assert ps.ps_ratio == 2.9654951768339957
        assert ps.net_margin == 0.08067342542287398
        assert ps.ev_to_sales == 2.90832573133584
        assert ps.pretax_operating_margin == 0.14397950144968602

        vebitda = rows["vebitda"]
        assert vebitda.number_of_firms == 24
        assert vebitda.ev_to_ebitda_rd_positive_ebitda == 15.297077571121077
        assert vebitda.ev_to_ebitda_positive_ebitda == 15.589298350244047
        assert vebitda.ev_to_ebit_positive_ebitda == 20.11940748200679
        assert vebitda.ev_to_after_tax_ebit_positive_ebitda == 27.45167095103594
        assert vebitda.ev_to_ebitda_rd_all == 16.664863306751414
        assert vebitda.ev_to_ebitda_all == 17.010864017994194
        assert vebitda.ev_to_ebit_all == 20.199581899178625
        assert vebitda.ev_to_after_tax_ebit_all == 27.561063920031707
    finally:
        db.close()


def test_pe_versions_preserve_changed_bytes_and_reactivate_history(
    monkeypatch,
    tmp_path: Path,
) -> None:
    raw = pd.DataFrame(
        [
            ["Industry Name", "Number of firms", "% of Money Losing firms (Trailing)", "Current PE", "Trailing PE", "Forward PE", "Aggregate Mkt Cap/ Net Income (all firms)", "Aggregate Mkt Cap/ Trailing Net Income (only money making firms)", "Expected growth - next 5 years", "PEG Ratio"],
            ["Advertising", 24, 0.1, 10.0, 11.0, 12.0, 9.0, 8.0, 0.2, 0.4],
        ]
    )
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_industry_averages",
        staticmethod(lambda path: raw),
    )
    source = tmp_path / "peIndia.xls"
    source.write_bytes(b"pe-version-one")
    first_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    db = _session()
    try:
        assert DamodaranBenchmarkIngestionService.ingest_pe_file(db, str(source), "India") == 1
        assert DamodaranBenchmarkIngestionService.ingest_pe_file(db, str(source), "India") == 1
        source.write_bytes(b"pe-version-two")
        assert DamodaranBenchmarkIngestionService.ingest_pe_file(db, str(source), "India") == 1
        versions = db.query(DamodaranDatasetFile).order_by(DamodaranDatasetFile.id).all()
        assert len(versions) == 2
        assert versions[0].source_sha256 == first_hash
        assert versions[0].is_active is False
        assert versions[1].is_active is True
        assert db.query(DamodaranPricingBenchmark).count() == 2

        source.write_bytes(b"pe-version-one")
        assert DamodaranBenchmarkIngestionService.ingest_pe_file(db, str(source), "India") == 1
        db.refresh(versions[0])
        db.refresh(versions[1])
        assert versions[0].is_active is True
        assert versions[1].is_active is False
        assert db.query(DamodaranPricingBenchmark).count() == 2
    finally:
        db.close()


@pytest.mark.parametrize(
    "importer",
    ["ingest_pe_file", "ingest_pbv_file", "ingest_ps_file", "ingest_vebitda_file"],
)
def test_pricing_importers_fail_closed_before_metadata(
    monkeypatch,
    tmp_path: Path,
    importer: str,
) -> None:
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_industry_averages",
        staticmethod(lambda path: pd.DataFrame([["Industry Name", "Wrong column"], ["Advertising", 1]])),
    )
    source = tmp_path / "pricing.xls"
    source.write_bytes(b"invalid-pricing")
    db = _session()
    try:
        with pytest.raises(ValueError, match="Missing required|header group"):
            getattr(DamodaranBenchmarkIngestionService, importer)(db, str(source), "India")
        assert db.query(DamodaranDatasetFile).count() == 0
        assert db.query(DamodaranPricingBenchmark).count() == 0
    finally:
        db.close()
