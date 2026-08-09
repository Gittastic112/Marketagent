import hashlib
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import (
    DamodaranCapexBenchmark,
    DamodaranDividendBenchmark,
    DamodaranFCFEBenchmark,
    DamodaranMarginBenchmark,
    DamodaranRoeBenchmark,
    DamodaranWcBenchmark,
)
from app.models.real_options import IndustryVolatilityBenchmark
from app.services.damodaran_ingestion import DamodaranBenchmarkIngestionService


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def _approved_source(filename: str) -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "damodaran" / "raw" / filename


def _assert_version(
    db,
    *,
    filename: str,
    expected_hash: str,
    expected_rows: int = 94,
) -> DamodaranDatasetFile:
    dataset = db.query(DamodaranDatasetFile).filter_by(uploaded_filename=filename).one()
    assert dataset.source_sha256 == expected_hash
    assert dataset.source_as_of == "2026-01-05"
    assert dataset.date_confidence == "high"
    assert dataset.import_kind == "typed"
    assert dataset.is_active is True
    assert dataset.row_count == expected_rows
    return dataset


def test_capex_ingestion_is_hash_idempotent_and_preserves_changed_versions(
    monkeypatch,
    tmp_path: Path,
) -> None:
    df_raw = pd.DataFrame(
        [
            ["Date updated:", "2026-01-05"],
            ["Industry Name", "Number of Firms", "Net Cap Ex/Sales", "Sales/ Invested Capital (LTM)"],
            ["Advertising", 24, 0.0039, 1.3308],
            ["Aerospace/Defense", 23, 0.0165, 1.8138],
        ]
    )
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_industry_averages",
        staticmethod(lambda path: df_raw),
    )
    source = tmp_path / "capexIndia.xls"
    source.write_bytes(b"capex-version-one")
    first_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    db = _session()
    try:
        first_count = DamodaranBenchmarkIngestionService.ingest_capex_file(
            db,
            str(source),
            "India",
        )
        same_hash_count = DamodaranBenchmarkIngestionService.ingest_capex_file(
            db,
            str(source),
            "India",
        )

        assert first_count == 2
        assert same_hash_count == 2
        assert db.query(DamodaranDatasetFile).count() == 1
        assert db.query(DamodaranCapexBenchmark).count() == 2

        first_version = db.query(DamodaranDatasetFile).one()
        assert first_version.source_sha256 == first_hash
        assert first_version.source_byte_size == len(b"capex-version-one")
        assert first_version.source_as_of == "2026-01-05"
        assert first_version.date_confidence == "high"
        assert first_version.canonical_source_path == "raw/datasets/capexIndia.xls"
        assert first_version.import_kind == "typed"
        assert first_version.is_active is True
        assert first_version.row_count == 2

        source.write_bytes(b"capex-version-two")
        changed_hash_count = DamodaranBenchmarkIngestionService.ingest_capex_file(
            db,
            str(source),
            "India",
        )

        assert changed_hash_count == 2
        assert db.query(DamodaranDatasetFile).count() == 2
        assert db.query(DamodaranCapexBenchmark).count() == 4
        versions = db.query(DamodaranDatasetFile).order_by(DamodaranDatasetFile.id).all()
        assert versions[0].is_active is False
        assert versions[0].superseded_at is not None
        assert versions[1].is_active is True
        assert versions[1].source_sha256 != first_hash

        source.write_bytes(b"capex-version-one")
        restored_count = DamodaranBenchmarkIngestionService.ingest_capex_file(
            db,
            str(source),
            "India",
        )
        assert restored_count == 2
        assert db.query(DamodaranDatasetFile).count() == 2
        assert db.query(DamodaranCapexBenchmark).count() == 4
        db.refresh(versions[0])
        db.refresh(versions[1])
        assert versions[0].is_active is True
        assert versions[0].superseded_at is None
        assert versions[1].is_active is False
        assert versions[1].superseded_at is not None
    finally:
        db.close()


def test_roe_ingestion_matches_approved_source_and_is_idempotent() -> None:
    source = _approved_source("roeIndia.xls")
    db = _session()
    try:
        first_count = DamodaranBenchmarkIngestionService.ingest_roe_file(
            db,
            str(source),
            "India",
        )
        second_count = DamodaranBenchmarkIngestionService.ingest_roe_file(
            db,
            str(source),
            "India",
        )

        assert first_count == 94
        assert second_count == 94
        assert db.query(DamodaranDatasetFile).count() == 1
        assert db.query(DamodaranRoeBenchmark).count() == 94

        dataset = db.query(DamodaranDatasetFile).one()
        assert dataset.source_sha256 == (
            "5608b78e268d7100c6d1ce171b8ee31913317158f22305cb6316d445cb4b675d"
        )
        assert dataset.source_as_of == "2026-01-05"
        assert dataset.date_confidence == "high"
        assert dataset.canonical_source_path == "raw/datasets/roeIndia(1).xls"
        assert dataset.row_count == 94

        advertising = (
            db.query(DamodaranRoeBenchmark)
            .filter(DamodaranRoeBenchmark.industry_name == "Advertising")
            .one()
        )
        assert advertising.number_of_firms == 24
        assert advertising.roe == 0.07969239127453762
        assert advertising.rd_adjusted_roe == 0.07960337120241455
        assert advertising.roc is None
        assert advertising.roic is None

        air_transport = (
            db.query(DamodaranRoeBenchmark)
            .filter(DamodaranRoeBenchmark.industry_name == "Air Transport")
            .one()
        )
        assert air_transport.roe is None
        assert air_transport.rd_adjusted_roe is None
        assert (
            db.query(DamodaranRoeBenchmark)
            .filter(DamodaranRoeBenchmark.industry_name.like("Total Market%"))
            .count()
            == 0
        )
    finally:
        db.close()


def test_margin_ingestion_matches_approved_source_and_is_idempotent() -> None:
    source = _approved_source("marginIndia.xls")
    db = _session()
    try:
        assert DamodaranBenchmarkIngestionService.ingest_margin_file(db, str(source), "India") == 94
        assert DamodaranBenchmarkIngestionService.ingest_margin_file(db, str(source), "India") == 94
        assert db.query(DamodaranDatasetFile).count() == 1
        assert db.query(DamodaranMarginBenchmark).count() == 94
        _assert_version(
            db,
            filename="marginIndia.xls",
            expected_hash="48cb509eb2dc5a64649d20b84b0d15c7e05e1384fd93463afceba49734ef8934",
        )
        advertising = db.query(DamodaranMarginBenchmark).filter_by(industry_name="Advertising").one()
        assert advertising.number_of_firms == 24
        assert advertising.gross_margin == 0.40764461730972246
        assert advertising.net_margin == 0.08067342542287398
        assert advertising.ebit_margin == 0.14395264948575595
        assert advertising.ebitda_margin == 0.17096872494303614
        assert db.query(DamodaranMarginBenchmark).filter(
            DamodaranMarginBenchmark.industry_name.like("Total Market%")
        ).count() == 0
    finally:
        db.close()


def test_working_capital_ingestion_matches_approved_source_and_is_idempotent() -> None:
    source = _approved_source("wcdataIndia.xls")
    db = _session()
    try:
        assert DamodaranBenchmarkIngestionService.ingest_wc_file(db, str(source), "India") == 94
        assert DamodaranBenchmarkIngestionService.ingest_wc_file(db, str(source), "India") == 94
        assert db.query(DamodaranDatasetFile).count() == 1
        assert db.query(DamodaranWcBenchmark).count() == 94
        _assert_version(
            db,
            filename="wcdataIndia.xls",
            expected_hash="323c251a42e1fa91442ce386e3e46300b01c4a287fba22a7628cabcd0cb6f30e",
        )
        advertising = db.query(DamodaranWcBenchmark).filter_by(industry_name="Advertising").one()
        assert advertising.number_of_firms == 24
        assert advertising.non_cash_wc_to_sales == 0.36194930866742064
        air_transport = db.query(DamodaranWcBenchmark).filter_by(
            industry_name="Air Transport"
        ).one()
        assert air_transport.non_cash_wc_to_sales == -0.23223630349209676
        assert db.query(DamodaranWcBenchmark).filter(
            DamodaranWcBenchmark.industry_name.like("Total Market%")
        ).count() == 0
    finally:
        db.close()


def test_dividend_ingestion_matches_approved_source_and_is_idempotent() -> None:
    source = _approved_source("divfundIndia.xls")
    db = _session()
    try:
        assert DamodaranBenchmarkIngestionService.ingest_dividend_file(db, str(source), "India") == 94
        assert DamodaranBenchmarkIngestionService.ingest_dividend_file(db, str(source), "India") == 94
        assert db.query(DamodaranDatasetFile).count() == 1
        assert db.query(DamodaranDividendBenchmark).count() == 94
        _assert_version(
            db,
            filename="divfundIndia.xls",
            expected_hash="456e82546d6665d4ff692968a2fb7f6f1b7f057b4a83617b1eb9957d3c7d1a03",
        )
        advertising = db.query(DamodaranDividendBenchmark).filter_by(
            industry_name="Advertising"
        ).one()
        assert advertising.number_of_firms == 24
        assert advertising.payout_ratio == 0.01367550781282007
        assert advertising.dividend_yield == 0.0003720289509407719
        assert db.query(DamodaranDividendBenchmark).filter(
            DamodaranDividendBenchmark.industry_name.like("Total Market%")
        ).count() == 0
    finally:
        db.close()


def test_fcfe_ingestion_matches_approved_source_and_is_idempotent() -> None:
    source = _approved_source("divfcfeIndia.xls")
    db = _session()
    try:
        assert DamodaranBenchmarkIngestionService.ingest_fcfe_file(db, str(source), "India") == 94
        assert DamodaranBenchmarkIngestionService.ingest_fcfe_file(db, str(source), "India") == 94
        assert db.query(DamodaranDatasetFile).count() == 1
        assert db.query(DamodaranFCFEBenchmark).count() == 94
        _assert_version(
            db,
            filename="divfcfeIndia.xls",
            expected_hash="e85d5dc6b8c0b6f573be5bb8088ef0f45ea6ad413c45d86cc194759f51d5618d",
        )
        advertising = db.query(DamodaranFCFEBenchmark).filter_by(
            industry_name="Advertising"
        ).one()
        assert advertising.number_of_firms == 24
        assert advertising.net_income == 122.04300000000002
        assert advertising.fcfe_before_debt == 66.57699999999998
        assert advertising.fcfe_after_debt == 71.66999999999999
        assert advertising.fcfe == advertising.fcfe_after_debt
        assert advertising.capex_minus_depreciation is None
        assert advertising.change_in_wc is None
        assert advertising.net_debt_issued is None
        assert db.query(DamodaranFCFEBenchmark).filter(
            DamodaranFCFEBenchmark.industry_name.like("Total Market%")
        ).count() == 0
    finally:
        db.close()


def test_volatility_ingestion_matches_approved_source_and_is_idempotent() -> None:
    source = _approved_source("optvarIndia.xls")
    db = _session()
    try:
        assert DamodaranBenchmarkIngestionService.ingest_volatility_file(
            db, str(source), "India"
        ) == 94
        assert DamodaranBenchmarkIngestionService.ingest_volatility_file(
            db, str(source), "India"
        ) == 94
        assert db.query(DamodaranDatasetFile).count() == 1
        assert db.query(IndustryVolatilityBenchmark).count() == 94
        dataset = _assert_version(
            db,
            filename="optvarIndia.xls",
            expected_hash="763b4a907f9584395e5cba1bb428f064dd6a85ff90a08e0bfb80d919d97cb54b",
        )
        assert dataset.canonical_source_path == "raw/datasets/optvarIndia(1).xls"

        advertising = db.query(IndustryVolatilityBenchmark).filter_by(
            industry_name="Advertising"
        ).one()
        assert advertising.dataset_file_id == dataset.id
        assert advertising.number_of_firms == 24
        assert advertising.equity_standard_deviation == 0.49858701429950836
        assert advertising.firm_value_standard_deviation == 0.48009883228977474
        assert advertising.equity_value_weight == 0.9534799865939207
        assert advertising.debt_value_weight == 0.046520013406079246
        assert advertising.assumed_debt_to_equity_vol_ratio == 0.40
        assert advertising.assumed_debt_equity_correlation == 0.50
        assert advertising.data_date.isoformat() == "2026-01-05"

        utility = db.query(IndustryVolatilityBenchmark).filter_by(
            industry_name="Utility (General)"
        ).one()
        assert utility.number_of_firms == 0
        assert utility.equity_standard_deviation == 0.0
        assert utility.firm_value_standard_deviation is None
        assert utility.equity_value_weight is None
        assert utility.debt_value_weight is None
        assert db.query(IndustryVolatilityBenchmark).filter(
            IndustryVolatilityBenchmark.industry_name.like("Total Market%")
        ).count() == 0
    finally:
        db.close()


def test_volatility_ingestion_preserves_changed_versions_and_reactivates_history(
    monkeypatch,
    tmp_path: Path,
) -> None:
    raw = pd.DataFrame(
        [
            ["Relative Standard Deviation of Bonds =", None, None, 0.40, None, None],
            ["Correlation between stocks & bonds =", None, None, 0.50, None, None],
            [
                "Industry Name",
                "Number of Firms",
                "Std Deviation in Equity",
                "Std Deviation in Firm Value",
                "E/(D+E)",
                "D/(D+E)",
            ],
            ["Advertising", 24, 0.50, 0.48, 0.95, 0.05],
            ["Total Market", 100, 0.40, 0.35, 0.80, 0.20],
        ]
    )
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_industry_averages",
        staticmethod(lambda path: raw),
    )
    source = tmp_path / "optvarIndia.xls"
    source.write_bytes(b"volatility-version-one")
    first_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    db = _session()
    try:
        assert DamodaranBenchmarkIngestionService.ingest_volatility_file(
            db, str(source), "India"
        ) == 1
        assert DamodaranBenchmarkIngestionService.ingest_volatility_file(
            db, str(source), "India"
        ) == 1
        assert db.query(DamodaranDatasetFile).count() == 1
        assert db.query(IndustryVolatilityBenchmark).count() == 1

        source.write_bytes(b"volatility-version-two")
        assert DamodaranBenchmarkIngestionService.ingest_volatility_file(
            db, str(source), "India"
        ) == 1
        assert db.query(DamodaranDatasetFile).count() == 2
        assert db.query(IndustryVolatilityBenchmark).count() == 2
        versions = db.query(DamodaranDatasetFile).order_by(DamodaranDatasetFile.id).all()
        assert versions[0].source_sha256 == first_hash
        assert versions[0].is_active is False
        assert versions[1].is_active is True

        source.write_bytes(b"volatility-version-one")
        assert DamodaranBenchmarkIngestionService.ingest_volatility_file(
            db, str(source), "India"
        ) == 1
        assert db.query(DamodaranDatasetFile).count() == 2
        assert db.query(IndustryVolatilityBenchmark).count() == 2
        db.refresh(versions[0])
        db.refresh(versions[1])
        assert versions[0].is_active is True
        assert versions[1].is_active is False
    finally:
        db.close()


@pytest.mark.parametrize(
    ("filename", "importer", "expected_label"),
    [
        ("marginIndia.xls", "ingest_margin_file", "Gross Margin"),
        ("wcdataIndia.xls", "ingest_wc_file", "Non-cash WC/ Sales"),
        ("divfundIndia.xls", "ingest_dividend_file", "Dividend Payout"),
        ("divfcfeIndia.xls", "ingest_fcfe_file", r"FCFE \(before debt cash flows\)"),
        ("optvarIndia.xls", "ingest_volatility_file", "Std Deviation in Equity"),
    ],
)
def test_versioned_importers_fail_closed_before_creating_metadata(
    monkeypatch,
    tmp_path: Path,
    filename: str,
    importer: str,
    expected_label: str,
) -> None:
    source = tmp_path / filename
    source.write_bytes(b"missing-required-columns")
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_industry_averages",
        staticmethod(lambda path: pd.DataFrame([
            ["Industry Name", "Number of firms"],
            ["Advertising", 24],
        ])),
    )
    db = _session()
    try:
        with pytest.raises(ValueError, match=expected_label):
            getattr(DamodaranBenchmarkIngestionService, importer)(db, str(source), "India")
        assert db.query(DamodaranDatasetFile).count() == 0
    finally:
        db.close()


@pytest.mark.parametrize(
    ("filename", "importer", "headers"),
    [
        (
            "marginIndia.xls",
            "ingest_margin_file",
            [
                "Industry Name",
                "Number of firms",
                "Gross Margin",
                "Net Margin",
                "Pre-tax Unadjusted Operating Margin",
                "EBITDA/Sales",
            ],
        ),
        (
            "wcdataIndia.xls",
            "ingest_wc_file",
            ["Industry Name", "Number of firms", "Non-cash WC/ Sales"],
        ),
        (
            "divfundIndia.xls",
            "ingest_dividend_file",
            ["Industry Name", "Number of firms", "Dividend Payout", "Dividend Yield"],
        ),
        (
            "divfcfeIndia.xls",
            "ingest_fcfe_file",
            [
                "Industry name",
                "Number of firms",
                "Net Income",
                "FCFE (before debt cash flows)",
                "FCFE (after debt cash flows)",
            ],
        ),
    ],
)
def test_versioned_importers_reject_empty_sources_without_metadata(
    monkeypatch,
    tmp_path: Path,
    filename: str,
    importer: str,
    headers: list[str],
) -> None:
    source = tmp_path / filename
    source.write_bytes(b"headers-without-industry-rows")
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_industry_averages",
        staticmethod(lambda path: pd.DataFrame([headers])),
    )
    db = _session()
    try:
        with pytest.raises(ValueError, match="No industry"):
            getattr(DamodaranBenchmarkIngestionService, importer)(db, str(source), "India")
        assert db.query(DamodaranDatasetFile).count() == 0
    finally:
        db.close()


def test_roe_ingestion_fails_closed_when_required_columns_are_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "roeIndia.xls"
    source.write_bytes(b"invalid-roe-source")
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_industry_averages",
        staticmethod(lambda path: pd.DataFrame([
            ["Industry Name", "ROE (unadjusted)"],
            ["Advertising", 0.10],
        ])),
    )
    db = _session()
    try:
        try:
            DamodaranBenchmarkIngestionService.ingest_roe_file(db, str(source), "India")
            raise AssertionError("Expected missing-column validation")
        except ValueError as exc:
            assert "ROE (adjusted for R&D)" in str(exc)
        assert db.query(DamodaranDatasetFile).count() == 0
        assert db.query(DamodaranRoeBenchmark).count() == 0
    finally:
        db.close()


def test_volatility_ingestion_requires_source_assumptions_before_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "optvarIndia.xls"
    source.write_bytes(b"missing-source-assumptions")
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_industry_averages",
        staticmethod(lambda path: pd.DataFrame([
            [
                "Industry Name",
                "Number of Firms",
                "Std Deviation in Equity",
                "Std Deviation in Firm Value",
                "E/(D+E)",
                "D/(D+E)",
            ],
            ["Advertising", 24, 0.50, 0.48, 0.95, 0.05],
        ])),
    )
    db = _session()
    try:
        with pytest.raises(ValueError, match="Relative Standard Deviation of Bonds"):
            DamodaranBenchmarkIngestionService.ingest_volatility_file(
                db, str(source), "India"
            )
        assert db.query(DamodaranDatasetFile).count() == 0
        assert db.query(IndustryVolatilityBenchmark).count() == 0
    finally:
        db.close()


def test_volatility_ingestion_rejects_empty_source_without_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "optvarIndia.xls"
    source.write_bytes(b"volatility-headers-without-industries")
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_industry_averages",
        staticmethod(lambda path: pd.DataFrame([
            ["Relative Standard Deviation of Bonds =", None, None, 0.40, None, None],
            ["Correlation between stocks & bonds =", None, None, 0.50, None, None],
            [
                "Industry Name",
                "Number of Firms",
                "Std Deviation in Equity",
                "Std Deviation in Firm Value",
                "E/(D+E)",
                "D/(D+E)",
            ],
        ])),
    )
    db = _session()
    try:
        with pytest.raises(ValueError, match="No industry volatility records"):
            DamodaranBenchmarkIngestionService.ingest_volatility_file(
                db, str(source), "India"
            )
        assert db.query(DamodaranDatasetFile).count() == 0
        assert db.query(IndustryVolatilityBenchmark).count() == 0
    finally:
        db.close()
