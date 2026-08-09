from datetime import date

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.services.macro_context import (
    DEFAULT_CLASSIFICATION_SYSTEM,
    DEFAULT_CURRENCY_CONTEXT,
    DEFAULT_CURRENCY_VARIABLE_DESCRIPTION,
    DEFAULT_MACRO_COUNTRY,
    DEFAULT_MACRO_MARKET,
)
from app.services.macro_sensitivity_ingestion import MacroSensitivityIngestionService


def test_quarterly_period_label_is_normalized_from_damodaran_decimal_date():
    period_label, period_date = MacroSensitivityIngestionService.normalize_period(2025.09, "quarterly")

    assert period_label == "2025 Q3"
    assert period_date == date(2025, 9, 30)


def test_sector_sensitivity_parser_maps_firm_value_and_operating_income_blocks():
    df_raw = pd.DataFrame(
        [
            ["intro", None, None, None, None, None, None, None, None, None],
            [None, None, "Using firm value", None, None, None, "Using operating income", None, None, None],
            ["SIC", "Industry", "Duration", "Cyclicality", "Inflation", "Currency", "Duration", "Cyclicality", "Inflation", "Currency"],
            [5311, "Department Stores", 3.01009, -0.297745, 1.906778, 0.693889, 4.2, 0.5, -1.1, 2.2],
        ]
    )

    records = MacroSensitivityIngestionService.parse_sector_sensitivity_sheet(df_raw, "macrodur.xls")

    assert records == [
        {
            "source_file": "macrodur.xls",
            "market": DEFAULT_MACRO_MARKET,
            "country": DEFAULT_MACRO_COUNTRY,
            "classification_system": DEFAULT_CLASSIFICATION_SYSTEM,
            "currency_context": DEFAULT_CURRENCY_CONTEXT,
            "currency_variable_description": DEFAULT_CURRENCY_VARIABLE_DESCRIPTION,
            "sic_code": "5311",
            "industry_name": "Department Stores",
            "firm_value_duration": 3.01009,
            "firm_value_cyclicality": -0.297745,
            "firm_value_inflation": 1.906778,
            "firm_value_currency": 0.693889,
            "operating_income_duration": 4.2,
            "operating_income_cyclicality": 0.5,
            "operating_income_inflation": -1.1,
            "operating_income_currency": 2.2,
        }
    ]


def test_macro_sheet_parser_returns_source_scoped_observations():
    df_raw = pd.DataFrame(
        [
            ["Date", "T.Bond Rate", "Change in rate", "Real GDP"],
            [2025.12, 0.0418, 0.000192, 24111.83],
        ]
    )

    records = MacroSensitivityIngestionService.parse_macro_sheet(
        df_raw,
        source_file="macrodur.xls",
        frequency="quarterly",
    )

    assert records == [
        {
            "series_name": "macrodur.quarterly.t_bond_rate",
            "description": "T.Bond Rate from macrodur.xls",
            "frequency": "quarterly",
            "period_label": "2025 Q4",
            "date_recorded": date(2025, 12, 31),
            "value": 0.0418,
        },
        {
            "series_name": "macrodur.quarterly.change_in_rate",
            "description": "Change in rate from macrodur.xls",
            "frequency": "quarterly",
            "period_label": "2025 Q4",
            "date_recorded": date(2025, 12, 31),
            "value": 0.000192,
        },
        {
            "series_name": "macrodur.quarterly.real_gdp",
            "description": "Real GDP from macrodur.xls",
            "frequency": "quarterly",
            "period_label": "2025 Q4",
            "date_recorded": date(2025, 12, 31),
            "value": 24111.83,
        },
    ]


def test_sector_sensitivity_ingestion_replaces_existing_source_rows(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    records = [
        {
            "source_file": "macrodur.xls",
            "sic_code": "5311",
            "industry_name": "Department Stores",
            "firm_value_duration": 3.01009,
            "firm_value_cyclicality": -0.297745,
            "firm_value_inflation": 1.906778,
            "firm_value_currency": 0.693889,
            "operating_income_duration": 4.2,
            "operating_income_cyclicality": 0.5,
            "operating_income_inflation": -1.1,
            "operating_income_currency": 2.2,
        }
    ]
    monkeypatch.setattr(
        MacroSensitivityIngestionService,
        "parse_sector_sensitivity_workbook",
        staticmethod(lambda file_path: records),
    )

    db = TestingSessionLocal()
    try:
        first_count = MacroSensitivityIngestionService.ingest_sector_sensitivity_file(
            db, "/workspace/data/damodaran/raw/macrodur.xls"
        )
        second_count = MacroSensitivityIngestionService.ingest_sector_sensitivity_file(
            db, "/workspace/data/damodaran/raw/macrodur.xls"
        )

        assert first_count == 1
        assert second_count == 1
        assert db.query(SectorMacroSensitivityBenchmark).count() == 1
    finally:
        db.close()
