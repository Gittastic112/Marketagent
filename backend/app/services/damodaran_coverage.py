from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.models.accounting import DamodaranGoodwillBenchmark, DamodaranRdBenchmark
from app.models.damodaran import DamodaranDatasetFile
from app.models.assumption_methodology import AssumptionMethodValue
from app.models.damodaran_fundamentals import (
    CountryMarketStats,
    DamodaranCapexBenchmark,
    DamodaranDividendBenchmark,
    DamodaranFCFEBenchmark,
    DamodaranFinancingFlowsBenchmark,
    DamodaranGrowthBenchmark,
    DamodaranMarginBenchmark,
    DamodaranPricingBenchmark,
    DamodaranRoeBenchmark,
    DamodaranWcBenchmark,
)
from app.models.macro import MacroObservation, MacroSeries
from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.models.real_options import IndustryVolatilityBenchmark


ImplementationStatus = Literal["supported", "partial", "unsupported"]
IngestionStatus = Literal["ingested", "metadata_only", "not_ingested", "source_missing"]
FreshnessStatus = Literal[
    "current",
    "stale",
    "historical",
    "unknown",
    "user_assumed_recent",
]

INVENTORY_VERSION = "2026-09-22.1"
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data" / "damodaran" / "raw"
CURRENT_SOURCE_MAX_AGE_DAYS = 550


def _items(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split("|") if item.strip())


@dataclass(frozen=True)
class DamodaranCoverageSpec:
    source_filename: str
    canonical_path: str
    source_type: str
    metric_family: str
    geography: str
    source_as_of: str
    date_confidence: Literal["high", "medium", "low"]
    catalog_status: Literal["active", "historical_only"]
    implementation_status: ImplementationStatus
    ingestion_available: bool
    destination_tables: tuple[str, ...]
    supported_metrics: tuple[str, ...]
    missing_metrics: tuple[str, ...]
    limitations: tuple[str, ...]
    action_required: str


def _india(
    filename: str,
    canonical_path: str,
    metric_family: str,
    implementation_status: ImplementationStatus,
    *,
    ingestion_available: bool = False,
    destination_tables: str = "",
    supported_metrics: str = "",
    missing_metrics: str = "",
    limitations: str = "",
    geography: str = "India",
    action_required: str,
) -> DamodaranCoverageSpec:
    return DamodaranCoverageSpec(
        source_filename=filename,
        canonical_path=canonical_path,
        source_type="dataset",
        metric_family=metric_family,
        geography=geography,
        source_as_of="2026-01-05",
        date_confidence="high",
        catalog_status="active",
        implementation_status=implementation_status,
        ingestion_available=ingestion_available,
        destination_tables=_items(destination_tables),
        supported_metrics=_items(supported_metrics),
        missing_metrics=_items(missing_metrics),
        limitations=_items(limitations),
        action_required=action_required,
    )


DAMODARAN_APPLICATION_COVERAGE: tuple[DamodaranCoverageSpec, ...] = (
    _india(
        "DollarIndia.xls", "raw/datasets/DollarIndia.xls", "market scale", "unsupported",
        missing_metrics="market capitalization|revenue|operating income|enterprise value",
        limitations="Workbook is mirrored but has no source-specific parser or typed destination.",
        action_required="Define whether aggregate scale metrics are used by valuation diagnostics before adding ingestion.",
    ),
    _india(
        "EVAIndia.xls", "raw/datasets/EVAIndia.xls", "economic value added", "unsupported",
        missing_metrics="ROE spread|equity EVA|ROC spread|enterprise EVA|capital weights",
        limitations="No source-specific parser or typed EVA destination exists.",
        action_required="Add only after the product has an explicit EVA diagnostic workflow.",
    ),
    _india(
        "EmployeeIndia.xls", "raw/datasets/EmployeeIndia.xls", "employee efficiency", "unsupported",
        missing_metrics="employees|revenue per employee|market value per employee|stock compensation",
        limitations="No operating-efficiency benchmark contract exists.",
        action_required="Defer until employee-efficiency metrics are used in a company workflow.",
    ),
    _india(
        "MktCapIndia.xls", "raw/datasets/MktCapIndia.xls", "market capitalization history", "unsupported",
        missing_metrics="quarterly market-cap change|annual market-cap change",
        limitations="Historical pricing context has no typed destination or consumer.",
        action_required="Defer until point-in-time pricing attribution requires this history.",
    ),
    _india(
        "R&DIndia.xls", "raw/datasets/R&DIndia.xls", "R&D capitalization", "partial",
        destination_tables="industry_rd_benchmarks",
        missing_metrics="capitalized R&D|R&D to invested capital|current R&D to revenue|five-year R&D history|R&D CAGR",
        limitations="A destination table exists, but no source-specific importer populates it.",
        action_required="Implement a versioned R&D importer before using industry R&D priors.",
    ),
    _india(
        "betaIndia.xls", "raw/datasets/betaIndia.xls", "beta and operating risk", "partial",
        ingestion_available=True,
        destination_tables="assumption_method_values",
        supported_metrics="levered beta|unlevered beta|cash-corrected beta|versioned source provenance",
        missing_metrics="D/E|effective tax rate|cash to firm value|standard deviations|historical beta series",
        limitations="Imported betas are industry priors and still require review for company leverage and business mix.",
        action_required="Use the active source version as a reviewed prior; do not treat it as a company regression beta.",
    ),
    _india(
        "capexIndia.xls", "raw/datasets/capexIndia.xls", "reinvestment", "partial",
        ingestion_available=True,
        destination_tables="damodaran_industry_capex_benchmarks",
        supported_metrics="net capex to sales|sales to invested capital",
        missing_metrics="capital expenditures|depreciation and amortization|capex to depreciation|acquisitions|net R&D",
        limitations="The importer persists only the fields used by the current reinvestment prior.",
        action_required="Extend the typed schema before exposing the omitted reinvestment components.",
    ),
    _india(
        "countrystats.xls", "raw/datasets/countrystats.xls", "country pricing and scale", "supported",
        geography="Global",
        ingestion_available=True,
        destination_tables="country_market_stats",
        supported_metrics="firm count|market capitalization|total debt including leases|firm value|cash|enterprise value|PE|PEG|PBV|PS|cash to firm value|EV multiples|dividend yield|total dividends|source date|versioned source provenance",
        limitations="Country aggregates are pricing context, not company intrinsic-value inputs.",
        action_required="No implementation work required; preserve the active source version on every refresh.",
    ),
    _india(
        "countrytaxrates.xls", "raw/datasets/countrytaxrates.xls", "country tax rates", "partial",
        geography="Global",
        ingestion_available=True,
        destination_tables="assumption_method_values",
        supported_metrics="corporate tax rate|versioned source provenance",
        missing_metrics="global-minimum-tax-adjusted rate",
        limitations="Country marginal tax is a terminal-rate reference, not a substitute for reviewed company effective tax.",
        action_required="Use as a reviewed country prior and preserve the active source version.",
    ),
    _india(
        "dbtfundIndia.xls", "raw/datasets/dbtfundIndia.xls", "capital structure", "partial",
        destination_tables="damodaran_industry_financing_flows",
        missing_metrics="book and market debt ratios|lease-adjusted debt ratios|interest coverage|debt to EBITDA|institutional holdings",
        limitations="A related destination table exists, but no source-specific importer populates it.",
        action_required="Implement capital-structure ingestion before using industry debt priors.",
    ),
    _india(
        "debtdetailsIndia.xls", "raw/datasets/debtdetailsIndia.xls", "debt composition", "unsupported",
        missing_metrics="lease debt|conventional debt|interest expense|book interest rate|maturity mix|debt raised and repaid",
        limitations="No typed debt-composition benchmark destination exists.",
        action_required="Add only when debt-footnote diagnostics consume these fields.",
    ),
    _india(
        "divfcfeIndia.xls", "raw/datasets/divfcfeIndia.xls", "FCFE payout capacity", "partial",
        ingestion_available=True,
        destination_tables="damodaran_industry_fcfe_benchmarks",
        supported_metrics="firm count|net income|FCFE before debt cash flows|FCFE after debt cash flows|versioned source provenance",
        missing_metrics="dividends|payout|buybacks|stock issuance|cash-return ratios|cash to firm value",
        limitations="The source reports aggregate FCFE before and after debt cash flows; it does not expose separate capex less depreciation, working-capital change, or net debt issued fields.",
        action_required="Add distribution-policy fields only with an explicit cash-return diagnostic consumer.",
    ),
    _india(
        "divfundIndia.xls", "raw/datasets/divfundIndia.xls", "dividend policy", "partial",
        ingestion_available=True,
        destination_tables="damodaran_industry_dividend_benchmarks",
        supported_metrics="firm count|dividend yield|dividend payout|versioned source provenance",
        missing_metrics="special dividends|ROE|institutional holdings|stock-price volatility",
        limitations="Yield and payout are persisted; policy-driver columns remain intentionally omitted.",
        action_required="Use current fields as dated priors; add policy drivers only with an explicit consumer.",
    ),
    _india(
        "finflowsIndia.xls", "raw/datasets/finflowsIndia.xls", "financing flows", "supported",
        ingestion_available=True,
        destination_tables="damodaran_industry_financing_flows",
        supported_metrics="firm count|dividends|buybacks|equity issuance|net equity change|net equity change to book equity|debt raised|debt repaid|net debt change|net debt change to total debt|lease debt change|versioned source provenance",
        limitations="Industry aggregate financing flows are context only; company payout inputs still require company facts.",
        action_required="Use for financing-policy comparison, never as company cash-flow autofill.",
    ),
    _india(
        "fundgrEBIndia.xls", "raw/datasets/fundgrEBIndia(1).xls", "fundamental EBIT growth", "partial",
        destination_tables="damodaran_industry_fundamental_growth",
        missing_metrics="ROC|reinvestment rate|fundamental EBIT growth",
        limitations="A growth destination exists, but no source-specific importer populates it.",
        action_required="Implement growth ingestion before using sustainable EBIT-growth priors.",
    ),
    _india(
        "fundgrIndia.xls", "raw/datasets/fundgrIndia.xls", "fundamental EPS growth", "partial",
        destination_tables="damodaran_industry_fundamental_growth",
        missing_metrics="ROE|retention ratio|fundamental EPS growth",
        limitations="A growth destination exists, but no source-specific importer populates it.",
        action_required="Implement growth ingestion before using sustainable EPS-growth priors.",
    ),
    _india(
        "goodwillIndia.xls", "raw/datasets/goodwillIndia.xls", "goodwill diagnostics", "partial",
        destination_tables="industry_goodwill_benchmarks",
        missing_metrics="goodwill|change in goodwill|goodwill to assets|impairment|impairment to goodwill",
        limitations="A destination table exists, but no source-specific importer populates it.",
        action_required="Implement versioned goodwill ingestion before industry acquisition diagnostics.",
    ),
    _india(
        "histgrIndia.xls", "raw/datasets/histgrIndia.xls", "historical and expected growth", "supported",
        ingestion_available=True,
        destination_tables="damodaran_industry_fundamental_growth",
        supported_metrics="five-year net-income CAGR|five-year revenue CAGR|two-year expected revenue growth|five-year expected revenue growth|five-year expected EPS growth|versioned source provenance",
        limitations="Historical and consensus growth are evidence-backed priors, not automatic company forecasts.",
        action_required="Require review when applying these dated industry priors to a company forecast.",
    ),
    _india(
        "insholdGlobal.xls", "raw/datasets/insholdGlobal.xls", "global ownership", "unsupported",
        geography="Global",
        missing_metrics="CEO holdings|corporate holdings|institutional holdings|insider holdings",
        limitations="No typed ownership benchmark destination exists.",
        action_required="Add only when governance or regression workflows consume ownership benchmarks.",
    ),
    _india(
        "insholdIndia.xls", "raw/datasets/insholdIndia.xls", "India ownership", "unsupported",
        missing_metrics="CEO holdings|corporate holdings|institutional holdings|insider holdings",
        limitations="No typed ownership benchmark destination exists.",
        action_required="Add only when governance or regression workflows consume ownership benchmarks.",
    ),
    _india(
        "leaseeffectIndia.xls", "raw/datasets/leaseeffectIndia.xls", "lease normalization", "unsupported",
        missing_metrics="lease expense|lease debt|lease-adjusted debt ratios|lease-adjusted operating income|lease-adjusted ROIC|lease-adjusted margins",
        limitations="Company lease normalization exists conceptually, but this industry workbook is not ingested.",
        action_required="Add a typed lease benchmark only after company lease-footnote normalization is complete.",
    ),
    DamodaranCoverageSpec(
        source_filename="macro.xls",
        canonical_path="raw/datasets/macro.xls",
        source_type="dataset",
        metric_family="historical macro series",
        geography="United States",
        source_as_of="through 2009-12",
        date_confidence="high",
        catalog_status="historical_only",
        implementation_status="supported",
        ingestion_available=True,
        destination_tables=("macro_series", "macro_observations"),
        supported_metrics=("annual macro series", "quarterly macro series"),
        missing_metrics=(),
        limitations=("The data ends in 2009 and is not current macro context.",),
        action_required="Use only for historical methodology and regression support.",
    ),
    DamodaranCoverageSpec(
        source_filename="macrodur.xls",
        canonical_path="raw/models/macrodur.xls",
        source_type="model/tool",
        metric_family="macro sensitivity",
        geography="United States",
        source_as_of="1987-1997 sector regressions; macro tables through 2009",
        date_confidence="high",
        catalog_status="historical_only",
        implementation_status="partial",
        ingestion_available=True,
        destination_tables=("macro_series", "macro_observations", "sector_macro_sensitivity_benchmarks"),
        supported_metrics=("macro series", "sector duration", "cyclicality", "inflation sensitivity", "currency sensitivity"),
        missing_metrics=("modern re-estimation", "source currency-sign verification"),
        limitations=("Sector regressions use a small 1987-1997 sample and are methodology references.",),
        action_required="Do not present coefficients as current without a modern re-estimation.",
    ),
    _india(
        "marginIndia.xls", "raw/datasets/marginIndia.xls", "operating margins", "partial",
        ingestion_available=True,
        destination_tables="damodaran_industry_margin_benchmarks",
        supported_metrics="firm count|gross margin|EBITDA margin|pre-tax unadjusted operating margin|net margin|versioned source provenance",
        missing_metrics="lease-adjusted margin|R&D-adjusted margin|stock compensation to sales|lease expense to sales|cost components",
        limitations="The importer captures the exact pre-tax unadjusted operating margin and three other headline fields; normalization variants remain omitted.",
        action_required="Extend only when normalized margin selection can consume the omitted variants.",
    ),
    _india(
        "optvarIndia.xls", "raw/datasets/optvarIndia(1).xls", "option volatility", "supported",
        ingestion_available=True,
        destination_tables="industry_volatility_benchmarks",
        supported_metrics="firm count|equity volatility|firm-value volatility|equity weight|debt weight|debt-to-equity volatility ratio assumption|stock-bond correlation assumption|versioned source provenance",
        limitations="Industry volatility is a prior; company and project volatility still require review.",
        action_required="Use only as a reviewed prior and preserve the active source version in downstream work.",
    ),
    _india(
        "pbvIndia.xls", "raw/datasets/pbvIndia.xls", "price to book", "supported",
        ingestion_available=True,
        destination_tables="damodaran_industry_pricing_benchmarks",
        supported_metrics="firm count|price to book|ROE|EV to invested capital|ROIC|versioned source provenance",
        limitations="Industry returns and multiples are benchmark facts, not company-specific normalized returns.",
        action_required="Preserve active source provenance and compare company accounting definitions before use.",
    ),
    _india(
        "peIndia.xls", "raw/datasets/peIndia(1).xls", "price to earnings", "supported",
        ingestion_available=True,
        destination_tables="damodaran_industry_pricing_benchmarks",
        supported_metrics="firm count|money-losing share|current PE|trailing PE|forward PE|aggregate PE variants|expected five-year growth|PEG|versioned source provenance",
        limitations="PE is not applicable when company earnings are non-positive and PEG remains sensitive to the growth definition.",
        action_required="Use only with positive normalized earnings and retain the active source version.",
    ),
    _india(
        "psIndia.xls", "raw/datasets/psIndia(1).xls", "price to sales", "supported",
        ingestion_available=True,
        destination_tables="damodaran_industry_pricing_benchmarks",
        supported_metrics="firm count|price to sales|net margin|EV to sales|pre-tax operating margin|versioned source provenance",
        limitations="Sales multiples require comparable revenue recognition, margins, and capital intensity.",
        action_required="Review company margin and revenue definitions before applying the industry multiple.",
    ),
    DamodaranCoverageSpec(
        source_filename="ratings.xls",
        canonical_path="raw/models/ratings.xls",
        source_type="model/tool",
        metric_family="synthetic ratings",
        geography="Global",
        source_as_of="unknown",
        date_confidence="low",
        catalog_status="active",
        implementation_status="supported",
        ingestion_available=False,
        destination_tables=(),
        supported_metrics=(
            "large non-financial rating bounds",
            "small or risky firm rating bounds",
            "financial-service rating bounds",
            "default spreads",
            "versioned source provenance",
            "interest-coverage rating calculation service",
        ),
        missing_metrics=("operating-lease capitalization",),
        limitations=(
            "The source date is unknown and recency remains a user assumption.",
            "The WACC endpoint expects interest coverage to already include any required operating-lease adjustment.",
        ),
        action_required="Add the workbook's iterative operating-lease capitalization as a separate reviewed normalization workflow.",
    ),
    _india(
        "roeIndia.xls", "raw/datasets/roeIndia(1).xls", "return on equity", "supported",
        ingestion_available=True,
        destination_tables="damodaran_industry_roe_benchmarks",
        supported_metrics="firm count|unadjusted ROE|R&D-adjusted ROE|versioned source provenance",
        limitations="Accounting ROE is a benchmark prior, not terminal ROIC or economic return on capital.",
        action_required="No implementation work required; preserve source version on every refresh.",
    ),
    _india(
        "taxrateIndia.xls", "raw/datasets/taxrateIndia.xls", "industry tax rates", "partial",
        ingestion_available=True,
        destination_tables="assumption_method_values",
        supported_metrics="average effective tax rate across all companies|versioned source provenance",
        missing_metrics="taxable income|accrual taxes|cash taxes|cash to accrual taxes|money-making-company and aggregate variants",
        limitations="The imported effective rate is a reality check; terminal tax should normally use a reviewed marginal rate.",
        action_required="Review the company tax position before selecting the industry effective-rate prior.",
    ),
    _india(
        "totalbetaIndia.xls", "raw/datasets/totalbetaIndia.xls", "total beta", "unsupported",
        missing_metrics="levered beta|unlevered beta|market correlation|total levered beta|total unlevered beta",
        limitations="Total beta is not the default risk measure for a diversified public-equity investor.",
        action_required="Keep deferred unless an approved undiversified-investor workflow requires it.",
    ),
    _india(
        "vebitdaIndia.xls", "raw/datasets/vebitdaIndia(1).xls", "enterprise-value multiples", "supported",
        ingestion_available=True,
        destination_tables="damodaran_industry_pricing_benchmarks",
        supported_metrics="firm count|EV to R&D-adjusted EBITDA|EV to EBITDA|EV to EBIT|EV to after-tax EBIT|positive-denominator variants|all-firm variants|versioned source provenance",
        limitations="Positive-denominator and all-firm populations are distinct and must not be blended silently.",
        action_required="Preserve the source population choice and active version in every downstream calculation.",
    ),
    _india(
        "waccIndia.xls", "raw/datasets/waccIndia.xls", "cost of capital", "supported",
        ingestion_available=True,
        destination_tables="assumption_method_values",
        supported_metrics="equity risk premium|USD risk-free rate|inflation-parity INR risk-free rate|country default spread|industry cost of equity|capital weights|industry cost of debt|USD WACC|local-currency WACC|versioned source provenance",
        limitations="Industry WACC and component costs are priors; company capital structure and currency consistency still require review.",
        action_required="Use only as a dated benchmark with exact currency and source provenance.",
    ),
    _india(
        "wcdataIndia.xls", "raw/datasets/wcdataIndia.xls", "working capital", "partial",
        ingestion_available=True,
        destination_tables="damodaran_industry_working_capital_benchmarks",
        supported_metrics="firm count|non-cash working capital to sales|versioned source provenance",
        missing_metrics="receivables to sales|inventory to sales|payables to sales",
        limitations="The importer persists only the aggregate non-cash working-capital ratio.",
        action_required="Extend component fields only when working-capital diagnostics consume them.",
    ),
)


# These inspected US snapshots share the corresponding typed column contracts,
# not the India values or geography. Originals and exact dates stay independent.
_US_VARIANTS = (
    ("betaIndia.xls", "betasUS-2026-01-05.xls", "raw/datasets/betas.xls"),
    ("waccIndia.xls", "waccUS-2026-01-05.xls", "raw/datasets/waccUS-2026-01-05.xls"),
    ("marginIndia.xls", "marginUS-2026-01-05.xls", "raw/datasets/marginUS-2026-01-05.xls"),
    ("capexIndia.xls", "capexUS-2026-01-05.xls", "raw/datasets/capexUS-2026-01-05.xls"),
    ("roeIndia.xls", "roeUS-2026-01-05.xls", "raw/datasets/roe(1).xls"),
    ("wcdataIndia.xls", "wcdataUS-2026-01-05.xls", "raw/datasets/wcdata.xls"),
)
DAMODARAN_APPLICATION_COVERAGE += tuple(
    replace(next(spec for spec in DAMODARAN_APPLICATION_COVERAGE if spec.source_filename == original),
        source_filename=filename, canonical_path=canonical, geography="United States",
        **({"supported_metrics": _items("equity risk premium|USD workbook risk-free rate|workbook default spread|industry cost of equity|capital weights|industry cost of debt|USD WACC|versioned source provenance")}
           if original == "waccIndia.xls" else {}))
    for original, filename, canonical in _US_VARIANTS
)


_DATASET_ROW_MODELS: dict[str, type] = {
    "R&DIndia.xls": DamodaranRdBenchmark,
    "betaIndia.xls": AssumptionMethodValue,
    "capexIndia.xls": DamodaranCapexBenchmark,
    "countrystats.xls": CountryMarketStats,
    "countrytaxrates.xls": AssumptionMethodValue,
    "dbtfundIndia.xls": DamodaranFinancingFlowsBenchmark,
    "divfcfeIndia.xls": DamodaranFCFEBenchmark,
    "divfundIndia.xls": DamodaranDividendBenchmark,
    "finflowsIndia.xls": DamodaranFinancingFlowsBenchmark,
    "fundgrEBIndia.xls": DamodaranGrowthBenchmark,
    "fundgrIndia.xls": DamodaranGrowthBenchmark,
    "goodwillIndia.xls": DamodaranGoodwillBenchmark,
    "histgrIndia.xls": DamodaranGrowthBenchmark,
    "marginIndia.xls": DamodaranMarginBenchmark,
    "optvarIndia.xls": IndustryVolatilityBenchmark,
    "pbvIndia.xls": DamodaranPricingBenchmark,
    "peIndia.xls": DamodaranPricingBenchmark,
    "psIndia.xls": DamodaranPricingBenchmark,
    "roeIndia.xls": DamodaranRoeBenchmark,
    "taxrateIndia.xls": AssumptionMethodValue,
    "vebitdaIndia.xls": DamodaranPricingBenchmark,
    "waccIndia.xls": AssumptionMethodValue,
    "wcdataIndia.xls": DamodaranWcBenchmark,
}
_DATASET_ROW_MODELS.update({filename: _DATASET_ROW_MODELS[original] for original, filename, _ in _US_VARIANTS})


def _typed_record_count(
    db: Session,
    spec: DamodaranCoverageSpec,
    dataset_ids: tuple[int, ...],
) -> int:
    if spec.source_filename in {"macro.xls", "macrodur.xls"}:
        stem = Path(spec.source_filename).stem
        macro_count = int(
            db.scalar(
                select(func.count())
                .select_from(MacroObservation)
                .join(MacroSeries, MacroSeries.id == MacroObservation.series_id)
                .where(MacroSeries.name.like(f"{stem}.%"))
            )
            or 0
        )
        if spec.source_filename == "macrodur.xls":
            sector_count = int(
                db.scalar(
                    select(func.count())
                    .select_from(SectorMacroSensitivityBenchmark)
                    .where(SectorMacroSensitivityBenchmark.source_file == spec.source_filename)
                )
                or 0
            )
            return macro_count + sector_count
        return macro_count

    model = _DATASET_ROW_MODELS.get(spec.source_filename)
    if model is None or not dataset_ids:
        return 0
    return int(
        db.scalar(
            select(func.count())
            .select_from(model)
            .where(model.dataset_file_id.in_(dataset_ids))
        )
        or 0
    )


def _freshness_status(spec: DamodaranCoverageSpec, as_of_date: date) -> FreshnessStatus:
    if spec.source_filename == "ratings.xls":
        return "user_assumed_recent"
    if spec.catalog_status == "historical_only":
        return "historical"
    try:
        source_date = date.fromisoformat(spec.source_as_of)
    except ValueError:
        return "unknown"
    age_days = (as_of_date - source_date).days
    return "current" if age_days <= CURRENT_SOURCE_MAX_AGE_DAYS else "stale"


def build_damodaran_coverage_report(
    db: Session,
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    as_of_date: date | None = None,
) -> dict:
    report_date = as_of_date or date.today()
    dataset_files = list(db.scalars(select(DamodaranDatasetFile)))
    dataset_ids_by_filename: dict[str, tuple[int, ...]] = {}
    metadata_count_by_filename: dict[str, int] = {}
    versions_by_filename: dict[str, list[DamodaranDatasetFile]] = {}
    for record in dataset_files:
        metadata_count_by_filename[record.uploaded_filename] = (
            metadata_count_by_filename.get(record.uploaded_filename, 0) + 1
        )
        versions_by_filename.setdefault(record.uploaded_filename, []).append(record)
    for filename in metadata_count_by_filename:
        dataset_ids_by_filename[filename] = tuple(
            record.id
            for record in dataset_files
            if record.uploaded_filename == filename and record.is_active
        )

    rows: list[dict] = []
    for spec in DAMODARAN_APPLICATION_COVERAGE:
        mirror_path = data_root / spec.source_filename
        source_present = mirror_path.is_file()
        mirror_source_sha256 = sha256(mirror_path.read_bytes()).hexdigest() if source_present else None
        stored_versions = sorted(
            versions_by_filename.get(spec.source_filename, []),
            key=lambda record: record.id,
            reverse=True,
        )
        active_version = next((record for record in stored_versions if record.is_active), None)
        dataset_ids = dataset_ids_by_filename.get(spec.source_filename, ())
        typed_count = _typed_record_count(db, spec, dataset_ids)
        metadata_count = metadata_count_by_filename.get(spec.source_filename, 0)
        if active_version is None:
            provenance_status = "missing" if stored_versions else "not_available"
            hash_matches_mirror = None
        else:
            required_provenance = (
                bool(active_version.source_sha256),
                bool(
                    active_version.source_as_of
                    and active_version.source_as_of.casefold() != "unknown"
                ),
                bool(
                    active_version.date_confidence
                    and active_version.date_confidence.casefold() != "unknown"
                ),
                bool(active_version.canonical_source_path),
            )
            if not all(required_provenance):
                provenance_status = "partial" if any(required_provenance) else "missing"
            elif mirror_source_sha256 and active_version.source_sha256 != mirror_source_sha256:
                provenance_status = "hash_mismatch"
            else:
                provenance_status = "complete"
            hash_matches_mirror = (
                active_version.source_sha256 == mirror_source_sha256
                if active_version.source_sha256 and mirror_source_sha256
                else None
            )
        if not source_present:
            ingestion_status: IngestionStatus = "source_missing"
        elif typed_count > 0:
            ingestion_status = "ingested"
        elif metadata_count > 0:
            ingestion_status = "metadata_only"
        else:
            ingestion_status = "not_ingested"

        if ingestion_status == "source_missing":
            action = "Restore the application-mirror source before ingestion or audit."
        elif ingestion_status == "metadata_only":
            action = "Generic parsing created metadata only; implement or run typed source ingestion."
        elif ingestion_status == "not_ingested" and spec.ingestion_available:
            action = "Run the canonical Damodaran ingestion script and verify typed row counts."
        else:
            action = spec.action_required

        rows.append(
            {
                "source_filename": spec.source_filename,
                "canonical_path": spec.canonical_path,
                "source_type": spec.source_type,
                "metric_family": spec.metric_family,
                "geography": spec.geography,
                "source_as_of": spec.source_as_of,
                "date_confidence": spec.date_confidence,
                "catalog_status": spec.catalog_status,
                "claim_type": "Source Summary",
                "implementation_status": spec.implementation_status,
                "ingestion_available": spec.ingestion_available,
                "ingestion_status": ingestion_status,
                "source_present": source_present,
                "metadata_import_count": metadata_count,
                "typed_record_count": typed_count,
                "stored_version_count": len(stored_versions),
                "active_version_id": active_version.id if active_version else None,
                "active_source_sha256": active_version.source_sha256 if active_version else None,
                "active_source_as_of": active_version.source_as_of if active_version else None,
                "active_date_confidence": active_version.date_confidence if active_version else None,
                "active_import_kind": active_version.import_kind if active_version else None,
                "active_row_count": active_version.row_count if active_version else None,
                "mirror_source_sha256": mirror_source_sha256,
                "hash_matches_mirror": hash_matches_mirror,
                "provenance_status": provenance_status,
                "freshness_status": _freshness_status(spec, report_date),
                "destination_tables": list(spec.destination_tables),
                "supported_metrics": list(spec.supported_metrics),
                "missing_metrics": list(spec.missing_metrics),
                "limitations": list(spec.limitations),
                "action_required": action,
            }
        )

    implementation_counts = {
        status: sum(row["implementation_status"] == status for row in rows)
        for status in ("supported", "partial", "unsupported")
    }
    ingestion_counts = {
        status: sum(row["ingestion_status"] == status for row in rows)
        for status in ("ingested", "metadata_only", "not_ingested", "source_missing")
    }
    freshness_counts = {
        status: sum(row["freshness_status"] == status for row in rows)
        for status in ("current", "stale", "historical", "unknown", "user_assumed_recent")
    }
    provenance_counts = {
        status: sum(row["provenance_status"] == status for row in rows)
        for status in ("complete", "partial", "missing", "not_available", "hash_mismatch")
    }
    warnings = []
    if implementation_counts["unsupported"]:
        warnings.append(
            f'{implementation_counts["unsupported"]} mirrored source(s) have no typed application support.'
        )
    if ingestion_counts["not_ingested"]:
        warnings.append(
            f'{ingestion_counts["not_ingested"]} present source(s) have no typed rows in the database.'
        )
    if ingestion_counts["metadata_only"]:
        warnings.append(
            f'{ingestion_counts["metadata_only"]} source(s) have metadata-only imports that are not usable benchmarks.'
        )
    if ingestion_counts["source_missing"]:
        warnings.append(
            f'{ingestion_counts["source_missing"]} expected application-mirror source(s) are missing.'
        )
    if freshness_counts["unknown"]:
        warnings.append(
            f'{freshness_counts["unknown"]} source(s) have unknown or non-comparable dates.'
        )
    if provenance_counts["partial"] or provenance_counts["missing"]:
        warnings.append(
            f'{provenance_counts["partial"] + provenance_counts["missing"]} stored source(s) lack complete version provenance.'
        )
    if provenance_counts["hash_mismatch"]:
        warnings.append(
            f'{provenance_counts["hash_mismatch"]} active source version(s) do not match the runtime mirror hash.'
        )

    return {
        "inventory_version": INVENTORY_VERSION,
        "generated_at": datetime.now(UTC),
        "source_count": len(rows),
        "source_present_count": sum(row["source_present"] for row in rows),
        "supported_count": implementation_counts["supported"],
        "partial_count": implementation_counts["partial"],
        "unsupported_count": implementation_counts["unsupported"],
        "ingested_count": ingestion_counts["ingested"],
        "metadata_only_count": ingestion_counts["metadata_only"],
        "not_ingested_count": ingestion_counts["not_ingested"],
        "source_missing_count": ingestion_counts["source_missing"],
        "current_count": freshness_counts["current"],
        "stale_count": freshness_counts["stale"],
        "historical_count": freshness_counts["historical"],
        "unknown_date_count": freshness_counts["unknown"],
        "user_assumed_recent_count": freshness_counts["user_assumed_recent"],
        "typed_record_count": sum(row["typed_record_count"] for row in rows),
        "provenance_complete_count": provenance_counts["complete"],
        "provenance_partial_count": provenance_counts["partial"],
        "provenance_missing_count": provenance_counts["missing"],
        "provenance_hash_mismatch_count": provenance_counts["hash_mismatch"],
        "warnings": warnings,
        "limitations": [
            "Coverage is limited to the 35-workbook application mirror; articles, case files, and regression PDFs are tracked separately.",
            "Typed row counts prove persistence, not semantic correctness or current suitability.",
            "Generic workbook parsing is metadata-only unless a source-specific importer persists reviewed fields.",
            "Freshness uses the catalog source date, never the database import timestamp.",
            "Capex, ROE, Margin, Working Capital, Dividend, FCFE, and Volatility use the hash-idempotent preserved-version lifecycle; remaining legacy importers are queued for conversion.",
        ],
        "rows": rows,
    }
