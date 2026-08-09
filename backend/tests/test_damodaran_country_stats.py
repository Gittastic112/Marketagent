import hashlib
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import CountryMarketStats
from app.services.damodaran_ingestion import DamodaranBenchmarkIngestionService


SOURCE_HASH = "900b6594f808461f9ce5194abf1a50e66f22854bc998473ad8282037d464829b"
HEADERS = [
    "Country",
    "count",
    "sum(Market Cap (in US $))",
    "sum(Total Debt incl leases (in US $))",
    "sum(Firm Value (in US $))",
    "sum(Cash)",
    "sum(Enterprise Value (in US $))",
    "median(Current PE)",
    "median(Trailing PE)",
    "median(Forward PE)",
    "median(PEG)",
    "median(PBV)",
    "median(PS)",
    "median(Cash/ Firm Value)",
    "median(EV/EBIT)",
    "median(EV/EBITDA)",
    "median(EV/Invested Capital)",
    "median(EV/Sales)",
    "Dividend Yield",
    None,
    None,
    "sum(Dividends)",
]


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def _source() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "damodaran" / "raw" / "countrystats.xls"


def test_country_stats_ingestion_is_exact_versioned_and_idempotent() -> None:
    db = _session()
    try:
        assert DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(_source())) == 127
        assert DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(_source())) == 127
        version = db.query(DamodaranDatasetFile).one()
        assert version.dataset_code == "countrystats"
        assert version.country == "Global"
        assert version.source_sha256 == SOURCE_HASH
        assert version.source_as_of == "2026-01-05"
        assert version.date_confidence == "high"
        assert version.canonical_source_path == "raw/datasets/countrystats.xls"
        assert version.import_kind == "typed"
        assert version.is_active is True
        assert version.row_count == 127
        assert db.query(CountryMarketStats).count() == 127
    finally:
        db.close()


def test_country_stats_ingestion_preserves_complete_india_row() -> None:
    db = _session()
    try:
        DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(_source()))
        india = db.query(CountryMarketStats).filter_by(country="India").one()
        assert india.firm_count == 4520
        assert india.market_cap_usd_millions == 4013915.843
        assert india.total_debt_usd_millions == 698017.6711204761
        assert india.firm_value_usd_millions == 4711933.552120477
        assert india.cash_usd_millions == 138028.824
        assert india.enterprise_value_usd_millions == 4573904.582120475
        assert india.median_current_pe == 25.59375
        assert india.median_trailing_pe == 24.80700280112045
        assert india.median_forward_pe == 28.03846153846154
        assert india.median_peg == 2.027938850817079
        assert india.median_pbv == 2.150406504065041
        assert india.median_ps == 1.709388971684054
        assert india.median_cash_to_firm_value == 0.01591915836101883
        assert india.median_ev_ebit == 19.88820754716981
        assert india.median_ev_ebitda == 15.99173553719008
        assert india.median_ev_invested_capital == 1.943747094374709
        assert india.median_ev_sales == 2.019546742209632
        assert india.dividend_yield == 0.01151727229424127
        assert india.total_dividends_usd_millions == -46229.36172999999
        assert india.date_updated.isoformat() == "2026-01-05T00:00:00"
    finally:
        db.close()


def test_country_stats_preserves_changed_versions_and_reactivates_history(
    monkeypatch,
    tmp_path: Path,
) -> None:
    raw = pd.DataFrame([HEADERS, ["India", 1] + [0.0] * 20])
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_country_stats",
        staticmethod(lambda path: raw),
        raising=False,
    )
    source = tmp_path / "countrystats.xls"
    source.write_bytes(b"country-version-one")
    first_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    db = _session()
    try:
        assert DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(source)) == 1
        assert DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(source)) == 1
        source.write_bytes(b"country-version-two")
        assert DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(source)) == 1
        versions = db.query(DamodaranDatasetFile).order_by(DamodaranDatasetFile.id).all()
        assert len(versions) == 2
        assert versions[0].source_sha256 == first_hash
        assert versions[0].is_active is False
        assert versions[1].is_active is True
        assert db.query(CountryMarketStats).count() == 2

        source.write_bytes(b"country-version-one")
        assert DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(source)) == 1
        db.refresh(versions[0])
        db.refresh(versions[1])
        assert versions[0].is_active is True
        assert versions[1].is_active is False
    finally:
        db.close()


def test_country_stats_fails_closed_before_creating_metadata(monkeypatch, tmp_path: Path) -> None:
    invalid_headers = [*HEADERS]
    invalid_headers[1] = "Wrong"
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_country_stats",
        staticmethod(
            lambda path: pd.DataFrame(
                [
                    invalid_headers,
                    ["India", 1, *([0.0] * 20)],
                ]
            )
        ),
        raising=False,
    )
    source = tmp_path / "countrystats.xls"
    source.write_bytes(b"invalid-country-source")
    db = _session()
    try:
        with pytest.raises(ValueError, match="Missing required country-statistics column"):
            DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(source))
        assert db.query(DamodaranDatasetFile).count() == 0
        assert db.query(CountryMarketStats).count() == 0
    finally:
        db.close()


def test_country_stats_rejects_unexpected_columns_before_creating_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    raw = pd.DataFrame(
        [
            [*HEADERS, "Unexpected"],
            ["India", 1, *([0.0] * 21)],
        ]
    )
    monkeypatch.setattr(
        DamodaranBenchmarkIngestionService,
        "_read_country_stats",
        staticmethod(lambda path: raw),
        raising=False,
    )
    source = tmp_path / "countrystats.xls"
    source.write_bytes(b"invalid-country-source-extra-column")
    db = _session()
    try:
        with pytest.raises(ValueError, match="exact country-statistics layout of 22 columns"):
            DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(source))
        assert db.query(DamodaranDatasetFile).count() == 0
        assert db.query(CountryMarketStats).count() == 0
    finally:
        db.close()
