import pandas as pd
import math
from datetime import date, datetime
from typing import Any
from sqlalchemy.orm import Session
from pathlib import Path
from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import (
    DamodaranMarginBenchmark,
    DamodaranCapexBenchmark,
    DamodaranWcBenchmark,
    DamodaranRoeBenchmark,
    DamodaranGrowthBenchmark,
    DamodaranDividendBenchmark,
    DamodaranFCFEBenchmark,
    DamodaranPricingBenchmark,
    CountryMarketStats,
)
from app.models.real_options import IndustryVolatilityBenchmark
from app.services.damodaran_dataset_versions import DamodaranDatasetVersionService


class DamodaranBenchmarkIngestionService:
    @staticmethod
    def _read_industry_averages(path: Path) -> pd.DataFrame:
        return pd.read_excel(str(path), engine='xlrd', sheet_name='Industry Averages', header=None)

    @staticmethod
    def _read_country_stats(path: Path) -> pd.DataFrame:
        return pd.read_excel(str(path), engine="xlrd", sheet_name=0, header=None)

    @staticmethod
    def _replace_existing_dataset(
        db: Session,
        *,
        path: Path,
        dataset_code: str,
        country: str,
        benchmark_model: type,
    ) -> None:
        existing_ids = [
            dataset_id
            for (dataset_id,) in (
                db.query(DamodaranDatasetFile.id)
                .filter(
                    DamodaranDatasetFile.uploaded_filename == path.name,
                    DamodaranDatasetFile.dataset_code == dataset_code,
                    DamodaranDatasetFile.country == country,
                )
                .all()
            )
        ]
        if not existing_ids:
            return

        db.query(benchmark_model).filter(benchmark_model.dataset_file_id.in_(existing_ids)).delete(
            synchronize_session=False
        )
        db.query(DamodaranDatasetFile).filter(DamodaranDatasetFile.id.in_(existing_ids)).delete(
            synchronize_session=False
        )
        db.commit()

    @staticmethod
    def _find_header_row(df: pd.DataFrame) -> int:
        """
        Dynamically find the row that contains 'Industry Name'.
        """
        for i in range(min(20, len(df))):
            row_values = df.iloc[i].astype(str).str.strip().str.lower().tolist()
            if "industry name" in row_values or "industry" in row_values:
                return i
        return 0 # fallback

    @staticmethod
    def _clean_value(val: Any) -> float | None:
        if pd.isna(val) or val == 'NA' or val == '':
            return None
        try:
            # If string with '%', convert to float
            if isinstance(val, str):
                val = val.replace('%', '').replace(',', '').strip()
            # if it's already a float but nan/inf
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                return None
            return f
        except ValueError:
            return None

    @staticmethod
    def _prepare_industry_frame(path: Path) -> pd.DataFrame:
        raw = DamodaranBenchmarkIngestionService._read_industry_averages(path)
        header_row = DamodaranBenchmarkIngestionService._find_header_row(raw)
        frame = raw.iloc[header_row + 1 :].copy()
        frame.columns = [str(column).strip() for column in raw.iloc[header_row]]
        return frame

    @staticmethod
    def _require_columns(
        frame: pd.DataFrame,
        *,
        source_label: str,
        required: dict[str, str],
    ) -> dict[str, str]:
        def normalize(value: str) -> str:
            return " ".join(value.split()).casefold()

        columns = {normalize(str(column)): str(column) for column in frame.columns}
        resolved = {
            key: columns.get(normalize(source_column))
            for key, source_column in required.items()
        }
        missing = [required[key] for key, column in resolved.items() if column is None]
        if missing:
            raise ValueError(
                f"Missing required {source_label} column(s): " + ", ".join(missing)
            )
        return {key: column for key, column in resolved.items() if column is not None}

    @staticmethod
    def _firm_count(value: Any) -> int | None:
        cleaned = DamodaranBenchmarkIngestionService._clean_value(value)
        return int(cleaned) if cleaned is not None else None

    @staticmethod
    def _require_labeled_value(
        raw: pd.DataFrame,
        *,
        source_label: str,
        row_label: str,
    ) -> float:
        normalized_label = " ".join(row_label.split()).casefold()
        matching_rows = []
        for index, row in raw.iterrows():
            first_cell = " ".join(str(row.iloc[0]).split()).casefold()
            if first_cell == normalized_label:
                matching_rows.append(index)
        if len(matching_rows) != 1:
            raise ValueError(
                f"Expected one {source_label} row labeled {row_label}; "
                f"found {len(matching_rows)}"
            )
        values = [
            cleaned
            for value in raw.loc[matching_rows[0]].iloc[1:]
            if (cleaned := DamodaranBenchmarkIngestionService._clean_value(value))
            is not None
        ]
        if len(values) != 1:
            raise ValueError(
                f"Expected one numeric {source_label} value for {row_label}; "
                f"found {len(values)}"
            )
        return values[0]

    @staticmethod
    def ingest_margin_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="margin",
            required={
                "industry": "Industry Name",
                "firm_count": "Number of firms",
                "gross_margin": "Gross Margin",
                "net_margin": "Net Margin",
                "operating_margin": "Pre-tax Unadjusted Operating Margin",
                "ebitda_margin": "EBITDA/Sales",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="margins",
            country=country,
            benchmark_model=DamodaranMarginBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(DamodaranMarginBenchmark(
                dataset_file_id=version.dataset_file.id,
                industry_name=industry,
                country=country,
                number_of_firms=DamodaranBenchmarkIngestionService._firm_count(
                    row[columns["firm_count"]]
                ),
                gross_margin=DamodaranBenchmarkIngestionService._clean_value(
                    row[columns["gross_margin"]]
                ),
                ebitda_margin=DamodaranBenchmarkIngestionService._clean_value(
                    row[columns["ebitda_margin"]]
                ),
                ebit_margin=DamodaranBenchmarkIngestionService._clean_value(
                    row[columns["operating_margin"]]
                ),
                net_margin=DamodaranBenchmarkIngestionService._clean_value(
                    row[columns["net_margin"]]
                ),
            ))
        if not records:
            db.rollback()
            raise ValueError(f"No industry margin records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_capex_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        df_raw = DamodaranBenchmarkIngestionService._read_industry_averages(path)
        header_row = DamodaranBenchmarkIngestionService._find_header_row(df_raw)
        df = df_raw.iloc[header_row+1:].copy()
        df.columns = [str(c).strip().lower() for c in df_raw.iloc[header_row]]

        ind_col = next((c for c in df.columns if 'industry' in c), None)
        capex_sales_col = next((c for c in df.columns if 'capex/sales' in c), None)
        net_capex_sales_col = next((c for c in df.columns if 'net capex/sales' in c or 'net cap ex/sales' in c), None)
        sales_capital_col = next((c for c in df.columns if 'sales/capital' in c or 'sales to capital' in c or 'sales/ invested capital' in c), None)

        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="capex",
            country=country,
            benchmark_model=DamodaranCapexBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0
        dataset_file = version.dataset_file

        records = []
        for _, row in df.iterrows():
            industry = str(row[ind_col]).strip()
            if not industry or industry == 'nan' or 'total' in industry.lower():
                continue
            records.append(DamodaranCapexBenchmark(
                dataset_file_id=dataset_file.id,
                industry_name=industry,
                country=country,
                capex_to_sales=DamodaranBenchmarkIngestionService._clean_value(row[capex_sales_col]) if capex_sales_col else None,
                net_capex_to_sales=DamodaranBenchmarkIngestionService._clean_value(row[net_capex_sales_col]) if net_capex_sales_col else None,
                sales_to_capital=DamodaranBenchmarkIngestionService._clean_value(row[sales_capital_col]) if sales_capital_col else None,
            ))
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_roe_file(db: Session, file_path: str, country: str) -> int:
        path = Path(file_path)
        df_raw = DamodaranBenchmarkIngestionService._read_industry_averages(path)
        header_row = DamodaranBenchmarkIngestionService._find_header_row(df_raw)
        df = df_raw.iloc[header_row + 1 :].copy()
        df.columns = [str(column).strip().lower() for column in df_raw.iloc[header_row]]

        industry_col = next((column for column in df.columns if "industry" in column), None)
        firm_count_col = next((column for column in df.columns if "number of firms" in column), None)
        unadjusted_roe_col = next(
            (column for column in df.columns if "roe" in column and "unadjusted" in column),
            None,
        )
        rd_adjusted_roe_col = next(
            (column for column in df.columns if "roe" in column and "adjusted for r&d" in column),
            None,
        )
        required = {
            "Industry Name": industry_col,
            "Number of firms": firm_count_col,
            "ROE (unadjusted)": unadjusted_roe_col,
            "ROE (adjusted for R&D)": rd_adjusted_roe_col,
        }
        missing = [label for label, column in required.items() if column is None]
        if missing:
            raise ValueError("Missing required ROE column(s): " + ", ".join(missing))

        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="roe",
            country=country,
            benchmark_model=DamodaranRoeBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records: list[DamodaranRoeBenchmark] = []
        for _, row in df.iterrows():
            industry = str(row[industry_col]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            firm_count = DamodaranBenchmarkIngestionService._clean_value(row[firm_count_col])
            records.append(
                DamodaranRoeBenchmark(
                    dataset_file_id=version.dataset_file.id,
                    industry_name=industry,
                    country=country,
                    number_of_firms=int(firm_count) if firm_count is not None else None,
                    roe=DamodaranBenchmarkIngestionService._clean_value(row[unadjusted_roe_col]),
                    rd_adjusted_roe=DamodaranBenchmarkIngestionService._clean_value(
                        row[rd_adjusted_roe_col]
                    ),
                )
            )

        if not records:
            db.rollback()
            raise ValueError(f"No industry ROE records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_wc_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="working-capital",
            required={
                "industry": "Industry Name",
                "firm_count": "Number of firms",
                "non_cash_wc_to_sales": "Non-cash WC/ Sales",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="working_capital",
            country=country,
            benchmark_model=DamodaranWcBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(DamodaranWcBenchmark(
                dataset_file_id=version.dataset_file.id,
                industry_name=industry,
                country=country,
                number_of_firms=DamodaranBenchmarkIngestionService._firm_count(
                    row[columns["firm_count"]]
                ),
                non_cash_wc_to_sales=DamodaranBenchmarkIngestionService._clean_value(
                    row[columns["non_cash_wc_to_sales"]]
                ),
            ))
        if not records:
            db.rollback()
            raise ValueError(f"No industry working-capital records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_dividend_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="dividend",
            required={
                "industry": "Industry Name",
                "firm_count": "Number of firms",
                "payout": "Dividend Payout",
                "yield": "Dividend Yield",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="dividends",
            country=country,
            benchmark_model=DamodaranDividendBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(DamodaranDividendBenchmark(
                dataset_file_id=version.dataset_file.id,
                industry_name=industry,
                country=country,
                number_of_firms=DamodaranBenchmarkIngestionService._firm_count(
                    row[columns["firm_count"]]
                ),
                dividend_yield=DamodaranBenchmarkIngestionService._clean_value(
                    row[columns["yield"]]
                ),
                payout_ratio=DamodaranBenchmarkIngestionService._clean_value(
                    row[columns["payout"]]
                ),
            ))
        if not records:
            db.rollback()
            raise ValueError(f"No industry dividend records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_fcfe_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="FCFE",
            required={
                "industry": "Industry name",
                "firm_count": "Number of firms",
                "net_income": "Net Income",
                "fcfe_before_debt": "FCFE (before debt cash flows)",
                "fcfe_after_debt": "FCFE (after debt cash flows)",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="fcfe",
            country=country,
            benchmark_model=DamodaranFCFEBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            fcfe_before_debt = DamodaranBenchmarkIngestionService._clean_value(
                row[columns["fcfe_before_debt"]]
            )
            fcfe_after_debt = DamodaranBenchmarkIngestionService._clean_value(
                row[columns["fcfe_after_debt"]]
            )
            records.append(DamodaranFCFEBenchmark(
                dataset_file_id=version.dataset_file.id,
                industry_name=industry,
                country=country,
                number_of_firms=DamodaranBenchmarkIngestionService._firm_count(
                    row[columns["firm_count"]]
                ),
                net_income=DamodaranBenchmarkIngestionService._clean_value(
                    row[columns["net_income"]]
                ),
                fcfe=fcfe_after_debt,
                fcfe_before_debt=fcfe_before_debt,
                fcfe_after_debt=fcfe_after_debt,
            ))
        if not records:
            db.rollback()
            raise ValueError(f"No industry FCFE records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_volatility_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        raw = DamodaranBenchmarkIngestionService._read_industry_averages(path)
        header_row = DamodaranBenchmarkIngestionService._find_header_row(raw)
        frame = raw.iloc[header_row + 1 :].copy()
        frame.columns = [str(column).strip() for column in raw.iloc[header_row]]
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="volatility",
            required={
                "industry": "Industry Name",
                "firm_count": "Number of Firms",
                "equity_standard_deviation": "Std Deviation in Equity",
                "firm_value_standard_deviation": "Std Deviation in Firm Value",
                "equity_value_weight": "E/(D+E)",
                "debt_value_weight": "D/(D+E)",
            },
        )
        debt_to_equity_vol_ratio = (
            DamodaranBenchmarkIngestionService._require_labeled_value(
                raw,
                source_label="volatility assumption",
                row_label="Relative Standard Deviation of Bonds =",
            )
        )
        debt_equity_correlation = (
            DamodaranBenchmarkIngestionService._require_labeled_value(
                raw,
                source_label="volatility assumption",
                row_label="Correlation between stocks & bonds =",
            )
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="volatility",
            country=country,
            benchmark_model=IndustryVolatilityBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0
        source_date = date.fromisoformat(version.dataset_file.source_as_of)

        records = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(
                IndustryVolatilityBenchmark(
                    dataset_file_id=version.dataset_file.id,
                    country=country,
                    data_date=source_date,
                    industry_name=industry,
                    number_of_firms=DamodaranBenchmarkIngestionService._firm_count(
                        row[columns["firm_count"]]
                    ),
                    equity_standard_deviation=DamodaranBenchmarkIngestionService._clean_value(
                        row[columns["equity_standard_deviation"]]
                    ),
                    firm_value_standard_deviation=DamodaranBenchmarkIngestionService._clean_value(
                        row[columns["firm_value_standard_deviation"]]
                    ),
                    equity_value_weight=DamodaranBenchmarkIngestionService._clean_value(
                        row[columns["equity_value_weight"]]
                    ),
                    debt_value_weight=DamodaranBenchmarkIngestionService._clean_value(
                        row[columns["debt_value_weight"]]
                    ),
                    assumed_debt_to_equity_vol_ratio=debt_to_equity_vol_ratio,
                    assumed_debt_equity_correlation=debt_equity_correlation,
                    source_file=path.name,
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No industry volatility records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_pe_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="PE",
            required={
                "industry": "Industry Name",
                "firm_count": "Number of firms",
                "percent_money_losing": "% of Money Losing firms (Trailing)",
                "pe_current": "Current PE",
                "pe_trailing": "Trailing PE",
                "pe_forward": "Forward PE",
                "pe_aggregate_all_firms": "Aggregate Mkt Cap/ Net Income (all firms)",
                "pe_aggregate_money_making": "Aggregate Mkt Cap/ Trailing Net Income (only money making firms)",
                "expected_growth": "Expected growth - next 5 years",
                "peg_ratio": "PEG Ratio",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="pe",
            country=country,
            benchmark_model=DamodaranPricingBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(
                DamodaranPricingBenchmark(
                    dataset_file_id=version.dataset_file.id,
                    industry_name=industry,
                    country=country,
                    number_of_firms=DamodaranBenchmarkIngestionService._firm_count(row[columns["firm_count"]]),
                    percent_money_losing=DamodaranBenchmarkIngestionService._clean_value(row[columns["percent_money_losing"]]),
                    pe_current=DamodaranBenchmarkIngestionService._clean_value(row[columns["pe_current"]]),
                    pe_trailing=DamodaranBenchmarkIngestionService._clean_value(row[columns["pe_trailing"]]),
                    pe_forward=DamodaranBenchmarkIngestionService._clean_value(row[columns["pe_forward"]]),
                    pe_aggregate_all_firms=DamodaranBenchmarkIngestionService._clean_value(row[columns["pe_aggregate_all_firms"]]),
                    pe_aggregate_money_making=DamodaranBenchmarkIngestionService._clean_value(row[columns["pe_aggregate_money_making"]]),
                    expected_growth_next_five_years=DamodaranBenchmarkIngestionService._clean_value(row[columns["expected_growth"]]),
                    peg_ratio=DamodaranBenchmarkIngestionService._clean_value(row[columns["peg_ratio"]]),
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No PE pricing records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db, dataset_file=version.dataset_file, row_count=len(records)
        )
        return len(records)

    @staticmethod
    def ingest_pbv_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="PBV",
            required={
                "industry": "Industry Name",
                "firm_count": "Number of firms",
                "pbv_ratio": "PBV",
                "roe": "ROE",
                "ev_to_invested_capital": "EV/ Invested Capital",
                "roic": "ROIC",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="pbv",
            country=country,
            benchmark_model=DamodaranPricingBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(
                DamodaranPricingBenchmark(
                    dataset_file_id=version.dataset_file.id,
                    industry_name=industry,
                    country=country,
                    number_of_firms=DamodaranBenchmarkIngestionService._firm_count(row[columns["firm_count"]]),
                    pbv_ratio=DamodaranBenchmarkIngestionService._clean_value(row[columns["pbv_ratio"]]),
                    roe=DamodaranBenchmarkIngestionService._clean_value(row[columns["roe"]]),
                    ev_to_invested_capital=DamodaranBenchmarkIngestionService._clean_value(row[columns["ev_to_invested_capital"]]),
                    roic=DamodaranBenchmarkIngestionService._clean_value(row[columns["roic"]]),
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No PBV pricing records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db, dataset_file=version.dataset_file, row_count=len(records)
        )
        return len(records)

    @staticmethod
    def ingest_ps_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="PS",
            required={
                "industry": "Industry Name",
                "firm_count": "Number of firms",
                "ps_ratio": "Price/Sales",
                "net_margin": "Net Margin",
                "ev_to_sales": "EV/Sales",
                "pretax_operating_margin": "Pre-tax Operating Margin",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="ps",
            country=country,
            benchmark_model=DamodaranPricingBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(
                DamodaranPricingBenchmark(
                    dataset_file_id=version.dataset_file.id,
                    industry_name=industry,
                    country=country,
                    number_of_firms=DamodaranBenchmarkIngestionService._firm_count(row[columns["firm_count"]]),
                    ps_ratio=DamodaranBenchmarkIngestionService._clean_value(row[columns["ps_ratio"]]),
                    net_margin=DamodaranBenchmarkIngestionService._clean_value(row[columns["net_margin"]]),
                    ev_to_sales=DamodaranBenchmarkIngestionService._clean_value(row[columns["ev_to_sales"]]),
                    pretax_operating_margin=DamodaranBenchmarkIngestionService._clean_value(row[columns["pretax_operating_margin"]]),
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No PS pricing records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db, dataset_file=version.dataset_file, row_count=len(records)
        )
        return len(records)

    @staticmethod
    def ingest_vebitda_file(db: Session, file_path: str, country: str):
        path = Path(file_path)
        raw = DamodaranBenchmarkIngestionService._read_industry_averages(path)
        header_row = DamodaranBenchmarkIngestionService._find_header_row(raw)
        expected_headers = [
            "industry name", "number of firms", "ev/ebitdar&d", "ev/ebitda",
            "ev/ebit", "ev/ebit (1-t)", "ev/ebitdar&d", "ev/ebitda",
            "ev/ebit", "ev/ebit (1-t)",
        ]
        actual_headers = [
            " ".join(str(value).split()).casefold() if pd.notna(value) else ""
            for value in raw.iloc[header_row].tolist()[:10]
        ]
        if actual_headers != expected_headers:
            raise ValueError("Missing required EV pricing columns or duplicate-column order")
        if header_row == 0:
            raise ValueError("Missing required EV pricing header group")
        group_headers = [
            " ".join(str(value).split()).casefold() if pd.notna(value) else ""
            for value in raw.iloc[header_row - 1].tolist()[:10]
        ]
        if group_headers[2] != "only positive ebitda firms" or group_headers[6] != "all firms":
            raise ValueError("Missing required EV pricing header group")

        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="vebitda",
            country=country,
            benchmark_model=DamodaranPricingBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records = []
        for _, row in raw.iloc[header_row + 1 :].iterrows():
            industry = str(row.iloc[0]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(
                DamodaranPricingBenchmark(
                    dataset_file_id=version.dataset_file.id,
                    industry_name=industry,
                    country=country,
                    number_of_firms=DamodaranBenchmarkIngestionService._firm_count(row.iloc[1]),
                    ev_to_ebitda_rd_positive_ebitda=DamodaranBenchmarkIngestionService._clean_value(row.iloc[2]),
                    ev_to_ebitda_positive_ebitda=DamodaranBenchmarkIngestionService._clean_value(row.iloc[3]),
                    ev_to_ebit_positive_ebitda=DamodaranBenchmarkIngestionService._clean_value(row.iloc[4]),
                    ev_to_after_tax_ebit_positive_ebitda=DamodaranBenchmarkIngestionService._clean_value(row.iloc[5]),
                    ev_to_ebitda_rd_all=DamodaranBenchmarkIngestionService._clean_value(row.iloc[6]),
                    ev_to_ebitda_all=DamodaranBenchmarkIngestionService._clean_value(row.iloc[7]),
                    ev_to_ebit_all=DamodaranBenchmarkIngestionService._clean_value(row.iloc[8]),
                    ev_to_after_tax_ebit_all=DamodaranBenchmarkIngestionService._clean_value(row.iloc[9]),
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No EV pricing records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db, dataset_file=version.dataset_file, row_count=len(records)
        )
        return len(records)

    @staticmethod
    def ingest_countrystats_file(db: Session, file_path: str):
        path = Path(file_path)
        raw = DamodaranBenchmarkIngestionService._read_country_stats(path)
        if raw.shape[1] != 22:
            raise ValueError(
                f"Expected exact country-statistics layout of 22 columns; found {raw.shape[1]}"
            )
        header_row = next(
            (
                index
                for index in range(min(20, len(raw)))
                if str(raw.iloc[index, 0]).strip().casefold() == "country"
            ),
            None,
        )
        if header_row is None:
            raise ValueError("Missing required country-statistics column: Country")

        required_columns = {
            0: "Country",
            1: "count",
            2: "sum(Market Cap (in US $))",
            3: "sum(Total Debt incl leases (in US $))",
            4: "sum(Firm Value (in US $))",
            5: "sum(Cash)",
            6: "sum(Enterprise Value (in US $))",
            7: "median(Current PE)",
            8: "median(Trailing PE)",
            9: "median(Forward PE)",
            10: "median(PEG)",
            11: "median(PBV)",
            12: "median(PS)",
            13: "median(Cash/ Firm Value)",
            14: "median(EV/EBIT)",
            15: "median(EV/EBITDA)",
            16: "median(EV/Invested Capital)",
            17: "median(EV/Sales)",
            18: "Dividend Yield",
            21: "sum(Dividends)",
        }

        def normalize(value: Any) -> str:
            return " ".join(str(value).split()).casefold()

        missing = [
            label
            for index, label in required_columns.items()
            if index >= raw.shape[1]
            or normalize(raw.iloc[header_row, index]) != normalize(label)
        ]
        if missing:
            raise ValueError(
                "Missing required country-statistics column(s): " + ", ".join(missing)
            )

        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="countrystats",
            country="Global",
            benchmark_model=CountryMarketStats,
        )
        if version.is_idempotent:
            return version.row_count or 0
        source_date = datetime.fromisoformat(version.dataset_file.source_as_of)

        records = []
        for _, row in raw.iloc[header_row + 1 :].iterrows():
            country_value = str(row.iloc[0]).strip()
            if not country_value or country_value == "nan" or "total" in country_value.casefold():
                continue
            records.append(
                CountryMarketStats(
                    dataset_file_id=version.dataset_file.id,
                    country=country_value,
                    firm_count=DamodaranBenchmarkIngestionService._firm_count(row.iloc[1]),
                    market_cap_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row.iloc[2]),
                    total_debt_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row.iloc[3]),
                    firm_value_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row.iloc[4]),
                    cash_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row.iloc[5]),
                    enterprise_value_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row.iloc[6]),
                    median_current_pe=DamodaranBenchmarkIngestionService._clean_value(row.iloc[7]),
                    median_trailing_pe=DamodaranBenchmarkIngestionService._clean_value(row.iloc[8]),
                    median_forward_pe=DamodaranBenchmarkIngestionService._clean_value(row.iloc[9]),
                    median_peg=DamodaranBenchmarkIngestionService._clean_value(row.iloc[10]),
                    median_pbv=DamodaranBenchmarkIngestionService._clean_value(row.iloc[11]),
                    median_ps=DamodaranBenchmarkIngestionService._clean_value(row.iloc[12]),
                    median_cash_to_firm_value=DamodaranBenchmarkIngestionService._clean_value(row.iloc[13]),
                    median_ev_ebit=DamodaranBenchmarkIngestionService._clean_value(row.iloc[14]),
                    median_ev_ebitda=DamodaranBenchmarkIngestionService._clean_value(row.iloc[15]),
                    median_ev_invested_capital=DamodaranBenchmarkIngestionService._clean_value(row.iloc[16]),
                    median_ev_sales=DamodaranBenchmarkIngestionService._clean_value(row.iloc[17]),
                    dividend_yield=DamodaranBenchmarkIngestionService._clean_value(row.iloc[18]),
                    total_dividends_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row.iloc[21]),
                    date_updated=source_date,
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No country-statistics records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)
