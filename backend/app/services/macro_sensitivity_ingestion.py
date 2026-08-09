import math
import re
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.macro import MacroObservation, MacroSeries
from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.services.macro_context import (
    DEFAULT_CLASSIFICATION_SYSTEM,
    DEFAULT_CURRENCY_CONTEXT,
    DEFAULT_CURRENCY_VARIABLE_DESCRIPTION,
    DEFAULT_MACRO_COUNTRY,
    DEFAULT_MACRO_MARKET,
)


class MacroSensitivityIngestionService:
    @staticmethod
    def normalize_column_name(value: Any) -> str:
        text = str(value).strip().lower()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        return re.sub(r"_+", "_", text).strip("_")

    @staticmethod
    def clean_float(value: Any) -> float | None:
        if pd.isna(value) or value == "":
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(parsed) or math.isinf(parsed):
            return None
        return parsed

    @staticmethod
    def normalize_period(raw_period: Any, frequency: str) -> tuple[str, date]:
        if frequency == "annual":
            year = int(float(raw_period))
            return str(year), date(year, 12, 31)

        raw_float = float(raw_period)
        year = int(raw_float)
        month = int(round((raw_float - year) * 100))
        if month > 100:
            year = int(str(int(raw_float))[:2])
            month = int(str(int(raw_float))[2:])
            year += 1900 if year >= 80 else 2000
        quarter_by_month = {3: 1, 6: 2, 9: 3, 12: 4}
        quarter = quarter_by_month.get(month)
        if quarter is None:
            raise ValueError(f"Unsupported quarterly period: {raw_period}")
        return f"{year} Q{quarter}", date(year, month, monthrange(year, month)[1])

    @staticmethod
    def parse_macro_sheet(
        df_raw: pd.DataFrame,
        *,
        source_file: str,
        frequency: str,
    ) -> list[dict[str, Any]]:
        headers = [str(column).strip() for column in df_raw.iloc[0].tolist()]
        rows = df_raw.iloc[1:].copy()
        records: list[dict[str, Any]] = []

        for _, row in rows.iterrows():
            raw_period = row.iloc[0]
            if pd.isna(raw_period):
                continue
            try:
                period_label, date_recorded = MacroSensitivityIngestionService.normalize_period(
                    raw_period, frequency
                )
            except (TypeError, ValueError):
                continue

            for column_index, header in enumerate(headers[1:], start=1):
                value = MacroSensitivityIngestionService.clean_float(row.iloc[column_index])
                if value is None or not header or header == "nan":
                    continue
                series_key = MacroSensitivityIngestionService.normalize_column_name(header)
                records.append(
                    {
                        "series_name": f"{Path(source_file).stem}.{frequency}.{series_key}",
                        "description": f"{header} from {source_file}",
                        "frequency": frequency,
                        "period_label": period_label,
                        "date_recorded": date_recorded,
                        "value": value,
                    }
                )
        return records

    @staticmethod
    def parse_macro_workbook(file_path: str) -> list[dict[str, Any]]:
        path = Path(file_path)
        annual = pd.read_excel(str(path), engine="xlrd", sheet_name="Annual Data", header=None)
        quarterly = pd.read_excel(str(path), engine="xlrd", sheet_name="Quarterly Data", header=None)
        return [
            *MacroSensitivityIngestionService.parse_macro_sheet(
                annual, source_file=path.name, frequency="annual"
            ),
            *MacroSensitivityIngestionService.parse_macro_sheet(
                quarterly, source_file=path.name, frequency="quarterly"
            ),
        ]

    @staticmethod
    def ingest_macro_file(db: Session, file_path: str) -> int:
        records = MacroSensitivityIngestionService.parse_macro_workbook(file_path)
        series_names = sorted({record["series_name"] for record in records})
        if not series_names:
            return 0

        existing_series = db.query(MacroSeries).filter(MacroSeries.name.in_(series_names)).all()
        series_by_name = {series.name: series for series in existing_series}
        for series_name in series_names:
            if series_name not in series_by_name:
                sample = next(record for record in records if record["series_name"] == series_name)
                series = MacroSeries(
                    name=series_name,
                    description=sample["description"],
                    units=None,
                    frequency=sample["frequency"],
                )
                db.add(series)
                db.flush()
                series_by_name[series_name] = series

        db.query(MacroObservation).filter(
            MacroObservation.series_id.in_([series_by_name[name].id for name in series_names])
        ).delete(synchronize_session=False)

        db.bulk_save_objects(
            [
                MacroObservation(
                    series_id=series_by_name[record["series_name"]].id,
                    date_recorded=record["date_recorded"],
                    value=record["value"],
                )
                for record in records
            ]
        )
        db.commit()
        return len(records)

    @staticmethod
    def parse_sector_sensitivity_sheet(
        df_raw: pd.DataFrame,
        source_file: str,
    ) -> list[dict[str, Any]]:
        header_row_idx = None
        for idx, row in df_raw.iterrows():
            row_values = [str(value).strip().lower() for value in row.tolist()]
            if "sic" in row_values and "industry" in row_values:
                header_row_idx = idx
                break
        if header_row_idx is None:
            raise ValueError("Could not find SIC header row in Sector Averages by SIC")

        records: list[dict[str, Any]] = []
        for _, row in df_raw.iloc[header_row_idx + 1 :].iterrows():
            sic = row.iloc[0]
            industry = row.iloc[1]
            if pd.isna(sic) or pd.isna(industry):
                continue
            records.append(
                {
                    "source_file": source_file,
                    "market": DEFAULT_MACRO_MARKET,
                    "country": DEFAULT_MACRO_COUNTRY,
                    "classification_system": DEFAULT_CLASSIFICATION_SYSTEM,
                    "currency_context": DEFAULT_CURRENCY_CONTEXT,
                    "currency_variable_description": DEFAULT_CURRENCY_VARIABLE_DESCRIPTION,
                    "sic_code": str(int(float(sic))) if MacroSensitivityIngestionService.clean_float(sic) is not None else str(sic).strip(),
                    "industry_name": str(industry).strip(),
                    "firm_value_duration": MacroSensitivityIngestionService.clean_float(row.iloc[2]),
                    "firm_value_cyclicality": MacroSensitivityIngestionService.clean_float(row.iloc[3]),
                    "firm_value_inflation": MacroSensitivityIngestionService.clean_float(row.iloc[4]),
                    "firm_value_currency": MacroSensitivityIngestionService.clean_float(row.iloc[5]),
                    "operating_income_duration": MacroSensitivityIngestionService.clean_float(row.iloc[6]),
                    "operating_income_cyclicality": MacroSensitivityIngestionService.clean_float(row.iloc[7]),
                    "operating_income_inflation": MacroSensitivityIngestionService.clean_float(row.iloc[8]),
                    "operating_income_currency": MacroSensitivityIngestionService.clean_float(row.iloc[9]),
                }
            )
        return records

    @staticmethod
    def parse_sector_sensitivity_workbook(file_path: str) -> list[dict[str, Any]]:
        path = Path(file_path)
        df_raw = pd.read_excel(str(path), engine="xlrd", sheet_name="Sector Averages by SIC", header=None)
        return MacroSensitivityIngestionService.parse_sector_sensitivity_sheet(df_raw, path.name)

    @staticmethod
    def ingest_sector_sensitivity_file(db: Session, file_path: str) -> int:
        path = Path(file_path)
        records = MacroSensitivityIngestionService.parse_sector_sensitivity_workbook(file_path)
        db.query(SectorMacroSensitivityBenchmark).filter(
            SectorMacroSensitivityBenchmark.source_file == path.name
        ).delete(synchronize_session=False)
        db.bulk_save_objects([SectorMacroSensitivityBenchmark(**record) for record in records])
        db.commit()
        return len(records)
