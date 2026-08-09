from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.damodaran import DamodaranDatasetFile
from app.services.industry_assumption import IndustryAssumptionService
from app.models.damodaran_fundamentals import (
    DamodaranMarginBenchmark,
    DamodaranCapexBenchmark,
    DamodaranWcBenchmark,
    DamodaranRoeBenchmark,
    DamodaranGrowthBenchmark,
    DamodaranFinancingFlowsBenchmark
)

class MockQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.result

class MockSession:
    def __init__(self, mocks):
        self.mocks = mocks

    def query(self, model):
        return MockQuery(self.mocks.get(model))

def test_get_assumption_priors():
    margin = DamodaranMarginBenchmark(ebit_margin=0.25, ebitda_margin=0.30)
    capex = DamodaranCapexBenchmark(sales_to_capital=1.5, net_capex_to_sales=0.05)
    roe = DamodaranRoeBenchmark(roc=0.15, roe=0.12)

    mock_db = MockSession({
        DamodaranMarginBenchmark: margin,
        DamodaranCapexBenchmark: capex,
        DamodaranRoeBenchmark: roe
    })

    priors = IndustryAssumptionService.get_assumption_priors(mock_db, country="India", industry="Software")

    assert "marginPriors" in priors
    assert priors["marginPriors"]["industryUnadjustedOperatingMargin"] == 0.25
    assert priors["marginPriors"]["industryLeaseRdAdjustedMargin"] == 0.30

    assert "reinvestmentPriors" in priors
    assert priors["reinvestmentPriors"]["industrySalesToCapital"] == 1.5
    assert priors["reinvestmentPriors"]["industryNetCapexToSales"] == 0.05

    assert "returnPriors" in priors
    assert priors["returnPriors"]["industryRoc"] == 0.15

    # Missing models should yield None
    assert priors["capitalStructurePriors"]["industryDebtSignals"] is None


def test_return_priors_use_only_the_active_roe_dataset_version() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        old = DamodaranDatasetFile(
            uploaded_filename="roeIndia.xls",
            dataset_code="roe",
            country="India",
            source_file_type="xls",
            source_sha256="a" * 64,
            source_as_of="2025-01-05",
            date_confidence="high",
            canonical_source_path="raw/datasets/roeIndia(1).xls",
            import_kind="typed",
            is_active=False,
            row_count=1,
        )
        current = DamodaranDatasetFile(
            uploaded_filename="roeIndia.xls",
            dataset_code="roe",
            country="India",
            source_file_type="xls",
            source_sha256="b" * 64,
            source_as_of="2026-01-05",
            date_confidence="high",
            canonical_source_path="raw/datasets/roeIndia(1).xls",
            import_kind="typed",
            is_active=True,
            row_count=1,
        )
        db.add_all([old, current])
        db.flush()
        db.add_all([
            DamodaranRoeBenchmark(
                dataset_file_id=old.id,
                industry_name="Advertising",
                country="India",
                roe=0.50,
                rd_adjusted_roe=0.45,
            ),
            DamodaranRoeBenchmark(
                dataset_file_id=current.id,
                industry_name="Advertising",
                country="India",
                roe=0.08,
                rd_adjusted_roe=0.079,
            ),
        ])
        db.commit()

        priors = IndustryAssumptionService.get_assumption_priors(
            db,
            country="India",
            industry="Advertising",
        )

        assert priors["returnPriors"] == {
            "industryRoc": None,
            "industryRoe": 0.08,
            "industryRoeAdjustedForRd": 0.079,
            "suggestedTerminalRoc": None,
        }
    finally:
        db.close()
