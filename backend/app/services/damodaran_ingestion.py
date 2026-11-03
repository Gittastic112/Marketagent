import pandas as pd
from datetime import date, datetime
from typing import Any
from sqlalchemy.orm import Session
from pathlib import Path
from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import DamodaranMarginBenchmark, DamodaranCapexBenchmark, DamodaranWcBenchmark, DamodaranRoeBenchmark, DamodaranGrowthBenchmark, DamodaranFinancingFlowsBenchmark, DamodaranDividendBenchmark, DamodaranFCFEBenchmark, DamodaranPricingBenchmark, CountryMarketStats
from app.models.assumption_methodology import AssumptionMethodValue
from app.models.real_options import IndustryVolatilityBenchmark
from app.services.damodaran_dataset_versions import DamodaranDatasetVersionService
from app.services.damodaran_workbook import (_read_industry_averages, _read_country_stats, _find_header_row, _clean_value, _require_columns, _firm_count, _require_labeled_value)

class DamodaranBenchmarkIngestionService:
    _read_industry_averages = staticmethod(_read_industry_averages)
    _read_country_stats = staticmethod(_read_country_stats)
    _find_header_row = staticmethod(_find_header_row)
    _clean_value = staticmethod(_clean_value)
    _require_columns = staticmethod(_require_columns)
    _firm_count = staticmethod(_firm_count)
    _require_labeled_value = staticmethod(_require_labeled_value)

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
    def _prepare_industry_frame(path: Path) -> pd.DataFrame:
        raw = DamodaranBenchmarkIngestionService._read_industry_averages(path)
        header_row = DamodaranBenchmarkIngestionService._find_header_row(raw)
        frame = raw.iloc[header_row + 1 :].copy()
        frame.columns = [str(column).strip() for column in raw.iloc[header_row]]
        return frame

    @staticmethod
    def _source_date(dataset_file: DamodaranDatasetFile) -> datetime | None:
        try:
            return datetime.fromisoformat(dataset_file.source_as_of or "")
        except ValueError:
            return None

    @staticmethod
    def _method_record(
        *,
        dataset_file: DamodaranDatasetFile,
        assumption_key: str,
        method_key: str,
        country: str,
        value: float,
        source_file: str,
        source_column: str,
        source_row: int | str,
        source_sheet: str = "Industry Averages",
        industry: str | None = None,
        currency: str | None = None,
        is_default: bool = False,
        source_type: str = "damodaran",
        notes: str | None = None,
    ) -> AssumptionMethodValue:
        return AssumptionMethodValue(
            dataset_file_id=dataset_file.id,
            assumption_key=assumption_key,
            method_key=method_key,
            country=country,
            industry=industry,
            currency=currency,
            value=value,
            unit="decimal",
            source_type=source_type,
            source_name="Damodaran January 2026 benchmark",
            source_file=source_file,
            source_sheet=source_sheet,
            source_row=str(source_row),
            source_column=source_column,
            dataset_date=DamodaranBenchmarkIngestionService._source_date(dataset_file),
            confidence="high",
            is_default_candidate=is_default,
            notes=notes,
        )

    @staticmethod
    def ingest_beta_methods_file(db: Session, file_path: str, country: str) -> int:
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="beta",
            required={
                "industry": "Industry Name",
                "beta": "Beta",
                "unlevered_beta": "Unlevered beta",
                "cash_corrected_beta": "Unlevered beta corrected for cash",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="beta_methods",
            country=country,
            benchmark_model=AssumptionMethodValue,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records: list[AssumptionMethodValue] = []
        methods = (
            ("industry_regression_beta", "beta", True),
            ("bottom_up_unlevered_beta", "unlevered_beta", False),
            ("cash_corrected_unlevered_beta", "cash_corrected_beta", False),
        )
        for index, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            for method_key, column_key, is_default in methods:
                value = DamodaranBenchmarkIngestionService._clean_value(
                    row[columns[column_key]]
                )
                if value is None:
                    continue
                records.append(
                    DamodaranBenchmarkIngestionService._method_record(
                        dataset_file=version.dataset_file,
                        assumption_key="beta",
                        method_key=method_key,
                        country=country,
                        industry=industry,
                        value=value,
                        source_file=path.name,
                        source_column=columns[column_key],
                        source_row=index + 1,
                        is_default=is_default,
                        notes=(
                            "Industry benchmark prior; review company leverage and business mix "
                            "before use."
                        ),
                    )
                )
        if not records:
            db.rollback()
            raise ValueError(f"No industry beta method records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_wacc_methods_file(db: Session, file_path: str, country: str) -> int:
        path = Path(file_path)
        raw = DamodaranBenchmarkIngestionService._read_industry_averages(path)
        is_us = country == "United States"
        if is_us and str(raw.iloc[2, 5]).strip() != "US companies":
            raise ValueError("US WACC requires an explicitly US-company source workbook")
        header_row = DamodaranBenchmarkIngestionService._find_header_row(raw)
        frame = raw.iloc[header_row + 1 :].copy()
        frame.columns = [str(column).strip() for column in raw.iloc[header_row]]
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="WACC",
            required={
                "industry": "Industry Name",
                "cost_of_equity": "Cost of Equity",
                "equity_to_capital": "E/(D+E)",
                "cost_of_debt": "Cost of Debt",
                "debt_to_capital": "D/(D+E)",
                "wacc_usd": "Cost of Capital",
                "wacc_local": "Cost of Capital (Local Currency)",
            },
        )
        usd_risk_free = DamodaranBenchmarkIngestionService._require_labeled_value(
            raw,
            source_label="WACC input",
            row_label="Long Term Treasury bond rate =",
            numeric_column=3,
        )
        equity_risk_premium = DamodaranBenchmarkIngestionService._require_labeled_value(
            raw,
            source_label="WACC input",
            row_label="Risk Premium to Use for Equity =",
            numeric_column=3,
        )
        country_default_spread = DamodaranBenchmarkIngestionService._require_labeled_value(
            raw,
            source_label="WACC input",
            row_label="Global Default Spread to add to cost of debt =",
            numeric_column=3,
        )
        local_inflation = DamodaranBenchmarkIngestionService._require_labeled_value(
            raw,
            source_label="WACC currency input",
            row_label="Expected inflation rate in local currency =" if is_us else "Expected inflation rate in Rupees =",
            numeric_column=2,
        )
        usd_inflation = DamodaranBenchmarkIngestionService._require_labeled_value(
            raw,
            source_label="WACC currency input",
            row_label="Expected inflation rate in US $ =",
            numeric_column=2,
        )
        local_risk_free = ((1 + usd_risk_free) * (1 + local_inflation) / (1 + usd_inflation)) - 1

        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="wacc_methods",
            country=country,
            benchmark_model=AssumptionMethodValue,
        )
        if version.is_idempotent:
            return version.row_count or 0

        records = [
            DamodaranBenchmarkIngestionService._method_record(
                dataset_file=version.dataset_file,
                assumption_key="equity_risk_premium",
                method_key="damodaran_us_workbook_erp" if is_us else "damodaran_country_erp",
                country=country,
                value=equity_risk_premium,
                source_file=path.name,
                source_column="Risk Premium to Use for Equity",
                source_row=10,
                is_default=True,
                notes=("Dated US WACC workbook equity premium. Review geographic exposure and reconcile the risk-free/default-spread convention; not a live premium."
                    if is_us else "Dated WACC workbook input; source labels it 'Global weighted average'. Review geographic exposure before use."),
            ),
            DamodaranBenchmarkIngestionService._method_record(
                dataset_file=version.dataset_file,
                assumption_key="risk_free_rate",
                method_key="long_term_us_treasury",
                country=country,
                currency="USD",
                value=usd_risk_free,
                source_file=path.name,
                source_column="Long Term Treasury bond rate",
                source_row=9,
                is_default=is_us,
                notes="USD risk-free input; do not apply directly to INR cash flows.",
            ),
            DamodaranBenchmarkIngestionService._method_record(
                dataset_file=version.dataset_file,
                assumption_key="risk_free_rate",
                method_key="inflation_parity_from_us_treasury",
                country=country,
                currency="INR",
                value=local_risk_free,
                source_file=path.name,
                source_column="Rows 9, 16, and 17",
                source_row="9,16,17",
                is_default=True,
                source_type="calculation",
                notes=(
                    "Calculation: (1 + USD Treasury rate) * (1 + INR inflation) / "
                    "(1 + USD inflation) - 1."
                ),
            ),
            DamodaranBenchmarkIngestionService._method_record(
                dataset_file=version.dataset_file,
                assumption_key="country_default_spread",
                method_key="damodaran_sovereign_default_spread",
                country=country,
                value=country_default_spread,
                source_file=path.name,
                source_column="Global Default Spread to add to cost of debt",
                source_row=11,
                is_default=True,
                notes=("Dated US WACC workbook default-spread input, not a company borrowing spread."
                    if is_us else "Dated WACC workbook input labeled 'Global weighted average', not verified country-specific risk."),
            ),
        ]
        if is_us:
            # The US workbook's optional conversion block is not an INR assumption.
            records = [record for record in records if record.currency != "INR"]
        for index, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            values = {
                key: DamodaranBenchmarkIngestionService._clean_value(row[column])
                for key, column in columns.items()
                if key != "industry"
            }
            local_cost_of_debt = (
                ((1 + values["cost_of_debt"]) * (1 + local_inflation) / (1 + usd_inflation)) - 1
                if values["cost_of_debt"] is not None
                else None
            )
            industry_methods = (
                ("cost_of_equity", "industry_cost_of_equity_usd", values["cost_of_equity"], "USD", False, columns["cost_of_equity"], None),
                ("pre_tax_cost_of_debt", "industry_cost_of_debt_usd", values["cost_of_debt"], "USD", False, columns["cost_of_debt"], None),
                ("pre_tax_cost_of_debt", "industry_cost_of_debt_local", local_cost_of_debt, "INR", True, columns["cost_of_debt"], "Converted by the workbook inflation-parity inputs."),
                ("debt_to_capital", "industry_market_debt_ratio", values["debt_to_capital"], None, True, columns["debt_to_capital"], None),
                ("equity_to_capital", "industry_market_equity_ratio", values["equity_to_capital"], None, True, columns["equity_to_capital"], None),
                ("wacc_start", "industry_cost_of_capital_usd", values["wacc_usd"], "USD", False, columns["wacc_usd"], None),
                ("wacc_start", "industry_cost_of_capital_local", values["wacc_local"], "INR", True, columns["wacc_local"], "Local-currency WACC calculated in the source workbook."),
            )
            for assumption_key, method_key, value, currency, is_default, source_column, notes in industry_methods:
                if value is None or (is_us and currency == "INR"):
                    continue
                records.append(
                    DamodaranBenchmarkIngestionService._method_record(
                        dataset_file=version.dataset_file,
                        assumption_key=assumption_key,
                        method_key=method_key,
                        country=country,
                        industry=industry,
                        currency=currency,
                        value=value,
                        source_file=path.name,
                        source_column=source_column,
                        source_row=index + 1,
                        is_default=is_default or (is_us and currency == "USD"),
                        source_type="calculation" if method_key == "industry_cost_of_debt_local" else "damodaran",
                        notes=notes,
                    )
                )
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_industry_tax_methods_file(db: Session, file_path: str, country: str) -> int:
        path = Path(file_path)
        raw = DamodaranBenchmarkIngestionService._read_industry_averages(path)
        header_row = DamodaranBenchmarkIngestionService._find_header_row(raw)
        headers = [" ".join(str(value).split()) for value in raw.iloc[header_row].tolist()]
        industry_index = next(i for i, value in enumerate(headers) if value.casefold() == "industry name")
        tax_index = next(i for i, value in enumerate(headers) if value.casefold() == "average across all companies")
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="industry_tax_methods",
            country=country,
            benchmark_model=AssumptionMethodValue,
        )
        if version.is_idempotent:
            return version.row_count or 0
        records: list[AssumptionMethodValue] = []
        for index in range(header_row + 1, len(raw)):
            industry = str(raw.iloc[index, industry_index]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            value = DamodaranBenchmarkIngestionService._clean_value(raw.iloc[index, tax_index])
            if value is None:
                continue
            records.append(
                DamodaranBenchmarkIngestionService._method_record(
                    dataset_file=version.dataset_file,
                    assumption_key="tax_rate",
                    method_key="industry_effective_tax_rate",
                    country=country,
                    industry=industry,
                    value=value,
                    source_file=path.name,
                    source_column=headers[tax_index],
                    source_row=index + 1,
                    is_default=True,
                    notes=(
                        "Industry effective tax-rate prior. Do not substitute mechanically "
                        "for a reviewed marginal terminal tax rate."
                    ),
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No industry tax method records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_country_tax_methods_file(db: Session, file_path: str) -> int:
        path = Path(file_path)
        raw = DamodaranBenchmarkIngestionService._read_country_stats(path)
        header_row = next(
            (
                index for index in range(min(20, len(raw)))
                if "country" in {
                    str(value).strip().casefold() for value in raw.iloc[index].tolist()
                }
            ),
            -1,
        )
        if header_row < 0:
            raise ValueError(f"Country tax header was not found in {file_path}")
        frame = raw.iloc[header_row + 1 :].copy()
        frame.columns = [str(column).strip() for column in raw.iloc[header_row]]
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="country tax",
            required={"country": "Country", "tax_rate": "Corporate Tax Rate"},
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="country_tax_methods",
            country="Global",
            benchmark_model=AssumptionMethodValue,
        )
        if version.is_idempotent:
            return version.row_count or 0
        records: list[AssumptionMethodValue] = []
        for index, row in frame.iterrows():
            country = str(row[columns["country"]]).strip()
            value = DamodaranBenchmarkIngestionService._clean_value(row[columns["tax_rate"]])
            if not country or country == "nan" or value is None:
                continue
            records.append(
                DamodaranBenchmarkIngestionService._method_record(
                    dataset_file=version.dataset_file,
                    assumption_key="tax_rate",
                    method_key="country_marginal_corporate_tax_rate",
                    country=country,
                    value=value,
                    source_file=path.name,
                    source_sheet=str(raw.columns.name or "Sheet1"),
                    source_column=columns["tax_rate"],
                    source_row=index + 1,
                    is_default=True,
                    notes="Country marginal corporate tax-rate benchmark.",
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No country tax method records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_growth_file(db: Session, file_path: str, country: str) -> int:
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="growth",
            required={
                "industry": "Industry Name",
                "historical_net_income_growth": "CAGR in Net Income- Last 5 years",
                "historical_revenue_growth": "CAGR in Revenues- Last 5 years",
                "expected_revenue_growth_2y": "Expected Growth in Revenues - Next 2 years",
                "expected_revenue_growth_5y": "Expected Growth in Revenues - Next 5 years",
                "expected_eps_growth": "Expected Growth in EPS - Next 5 years",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="historical_growth",
            country=country,
            benchmark_model=DamodaranGrowthBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0
        records: list[DamodaranGrowthBenchmark] = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(
                DamodaranGrowthBenchmark(
                    dataset_file_id=version.dataset_file.id,
                    industry_name=industry,
                    country=country,
                    historical_net_income_growth=DamodaranBenchmarkIngestionService._clean_value(row[columns["historical_net_income_growth"]]),
                    historical_revenue_growth=DamodaranBenchmarkIngestionService._clean_value(row[columns["historical_revenue_growth"]]),
                    expected_revenue_growth=DamodaranBenchmarkIngestionService._clean_value(row[columns["expected_revenue_growth_5y"]]),
                    expected_revenue_growth_2y=DamodaranBenchmarkIngestionService._clean_value(row[columns["expected_revenue_growth_2y"]]),
                    expected_revenue_growth_5y=DamodaranBenchmarkIngestionService._clean_value(row[columns["expected_revenue_growth_5y"]]),
                    expected_eps_growth=DamodaranBenchmarkIngestionService._clean_value(row[columns["expected_eps_growth"]]),
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No industry growth records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

    @staticmethod
    def ingest_financing_flows_file(db: Session, file_path: str, country: str) -> int:
        path = Path(file_path)
        frame = DamodaranBenchmarkIngestionService._prepare_industry_frame(path)
        columns = DamodaranBenchmarkIngestionService._require_columns(
            frame,
            source_label="financing flows",
            required={
                "industry": "Industry Name",
                "firm_count": "Number of Firms",
                "dividends": "Dividends in $ millions",
                "buybacks": "Buybacks in $ millions",
                "equity_issuance": "Equity Issuance in $ millions",
                "net_equity_change": "Net Equity Change in $ millions",
                "net_equity_change_ratio": "Net Equity Change as % of Book Equity",
                "debt_repaid": "Debt Repaid in $ millions",
                "debt_raised": "Debt Raised in $ millions",
                "net_debt_change": "Net Debt Change in $ millions",
                "net_debt_change_ratio": "Net Change in Debt as % of Total Debt",
                "lease_debt_change": "Change in Lease Debt in $ millions",
            },
        )
        version = DamodaranDatasetVersionService.begin_typed_import(
            db,
            path=path,
            dataset_code="financing_flows",
            country=country,
            benchmark_model=DamodaranFinancingFlowsBenchmark,
        )
        if version.is_idempotent:
            return version.row_count or 0
        records: list[DamodaranFinancingFlowsBenchmark] = []
        for _, row in frame.iterrows():
            industry = str(row[columns["industry"]]).strip()
            if not industry or industry == "nan" or "total" in industry.casefold():
                continue
            records.append(
                DamodaranFinancingFlowsBenchmark(
                    dataset_file_id=version.dataset_file.id,
                    industry_name=industry,
                    country=country,
                    number_of_firms=DamodaranBenchmarkIngestionService._firm_count(row[columns["firm_count"]]),
                    dividends_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row[columns["dividends"]]),
                    buybacks_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row[columns["buybacks"]]),
                    equity_issuance_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row[columns["equity_issuance"]]),
                    net_equity_change_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row[columns["net_equity_change"]]),
                    net_equity_change_to_book_equity=DamodaranBenchmarkIngestionService._clean_value(row[columns["net_equity_change_ratio"]]),
                    debt_repaid_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row[columns["debt_repaid"]]),
                    debt_raised_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row[columns["debt_raised"]]),
                    net_debt_change_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row[columns["net_debt_change"]]),
                    net_debt_change_to_total_debt=DamodaranBenchmarkIngestionService._clean_value(row[columns["net_debt_change_ratio"]]),
                    lease_debt_change_usd_millions=DamodaranBenchmarkIngestionService._clean_value(row[columns["lease_debt_change"]]),
                )
            )
        if not records:
            db.rollback()
            raise ValueError(f"No industry financing-flow records found in {file_path}")
        db.bulk_save_objects(records)
        DamodaranDatasetVersionService.complete_typed_import(
            db,
            dataset_file=version.dataset_file,
            row_count=len(records),
        )
        return len(records)

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
