from copy import deepcopy
from math import fsum, isfinite
from typing import Any

from sqlalchemy.orm import Session
from app.models.damodaran import DamodaranDatasetFile
from app.services.damodaran_dataset_versions import active_dataset_ids
from app.models.damodaran_fundamentals import (
    DamodaranMarginBenchmark,
    DamodaranCapexBenchmark,
    DamodaranWcBenchmark,
    DamodaranRoeBenchmark,
    DamodaranGrowthBenchmark,
    DamodaranFinancingFlowsBenchmark,
)


class IndustryAssumptionService:
    WEIGHTED_PRIOR_VERSION = 2

    @staticmethod
    def _source_summary(
        db: Session,
        module: str,
        label: str,
        record: Any | None,
    ) -> dict[str, Any] | None:
        if record is None:
            return None
        dataset_file_id = getattr(record, "dataset_file_id", None)
        dataset = (
            db.get(DamodaranDatasetFile, dataset_file_id)
            if dataset_file_id is not None and hasattr(db, "get")
            else None
        )
        return {
            "module": module,
            "source": label,
            "dataset_file_id": dataset_file_id,
            "source_file": dataset.uploaded_filename if dataset else None,
            "source_sha256": dataset.source_sha256 if dataset else None,
            "source_as_of": dataset.source_as_of if dataset else None,
            "canonical_source_path": dataset.canonical_source_path if dataset else None,
            "claim_type": "Estimate",
            "requires_review": True,
        }

    @staticmethod
    def get_assumption_priors(db: Session, country: str, industry: str) -> dict[str, Any]:
        """
        Fetches the unified assumption suggestion package for a given industry.
        This exactly matches the output format requested in Phase 3 / Phase 2 of the master plan.
        """
        active_ids = active_dataset_ids()
        margin_query = db.query(DamodaranMarginBenchmark).filter(
            DamodaranMarginBenchmark.industry_name == industry,
            DamodaranMarginBenchmark.dataset_file_id.in_(active_ids),
        )
        capex_query = db.query(DamodaranCapexBenchmark).filter(
            DamodaranCapexBenchmark.industry_name == industry,
            DamodaranCapexBenchmark.dataset_file_id.in_(active_ids),
        )
        wc_query = db.query(DamodaranWcBenchmark).filter(
            DamodaranWcBenchmark.industry_name == industry,
            DamodaranWcBenchmark.dataset_file_id.in_(active_ids),
        )
        roe_query = db.query(DamodaranRoeBenchmark).filter(
            DamodaranRoeBenchmark.industry_name == industry,
            DamodaranRoeBenchmark.dataset_file_id.in_(active_ids),
        )
        growth_query = db.query(DamodaranGrowthBenchmark).filter(
            DamodaranGrowthBenchmark.industry_name == industry,
            DamodaranGrowthBenchmark.dataset_file_id.in_(active_ids),
        )
        financing_query = db.query(DamodaranFinancingFlowsBenchmark).filter(
            DamodaranFinancingFlowsBenchmark.industry_name == industry,
            DamodaranFinancingFlowsBenchmark.dataset_file_id.in_(active_ids),
        )

        if country:
            margin_query = margin_query.filter(DamodaranMarginBenchmark.country == country)
            capex_query = capex_query.filter(DamodaranCapexBenchmark.country == country)
            wc_query = wc_query.filter(DamodaranWcBenchmark.country == country)
            roe_query = roe_query.filter(DamodaranRoeBenchmark.country == country)
            growth_query = growth_query.filter(DamodaranGrowthBenchmark.country == country)
            financing_query = financing_query.filter(DamodaranFinancingFlowsBenchmark.country == country)

        # Order by created_at desc to get the latest
        margin = margin_query.order_by(DamodaranMarginBenchmark.created_at.desc()).first()
        capex = capex_query.order_by(DamodaranCapexBenchmark.created_at.desc()).first()
        wc = wc_query.order_by(DamodaranWcBenchmark.created_at.desc()).first()
        roe = roe_query.order_by(DamodaranRoeBenchmark.created_at.desc()).first()
        growth = growth_query.order_by(DamodaranGrowthBenchmark.created_at.desc()).first()
        financing = financing_query.order_by(DamodaranFinancingFlowsBenchmark.created_at.desc()).first()

        source_summary = [item for item in (
            IndustryAssumptionService._source_summary(db, "margin", "Damodaran Industry Margin Benchmark", margin),
            IndustryAssumptionService._source_summary(db, "reinvestment", "Damodaran Industry Capex Benchmark", capex),
            IndustryAssumptionService._source_summary(db, "working_capital", "Damodaran Industry WC Benchmark", wc),
            IndustryAssumptionService._source_summary(db, "return", "Damodaran Industry ROE Benchmark", roe),
            IndustryAssumptionService._source_summary(db, "growth", "Damodaran Industry Growth Benchmark", growth),
            IndustryAssumptionService._source_summary(db, "financing", "Damodaran Industry Financing Benchmark", financing),
        ) if item is not None]
        version_ids = sorted({
            item["dataset_file_id"] for item in source_summary
            if item["dataset_file_id"] is not None
        })

        return {
            "country": country,
            "industry": industry,
            "dataVersion": {"activeDatasetFileIds": version_ids},
            "revenueGrowthPriors": {
                "companyHistorical": None,
                "industryHistorical5Y": growth.historical_revenue_growth if growth else None,
                "industryExpected2Y": growth.expected_revenue_growth_2y if growth else None,
                "industryExpected5Y": growth.expected_revenue_growth_5y if growth else None,
                "suggestedYears1To2": growth.expected_revenue_growth_2y if growth else None,
                "suggestedYears3To5": growth.expected_revenue_growth_5y if growth else None,
                "stableGrowthAnchor": None
            },
            "marginPriors": {
                "currentCompanyMargin": None,
                "industryUnadjustedOperatingMargin": margin.ebit_margin if margin else None,
                # The typed dataset has no lease/R&D-adjusted margin contract.
                "industryLeaseAdjustedMargin": None,
                "industryLeaseRdAdjustedMargin": None,
                "suggestedTargetMargin": margin.ebit_margin if margin else None
            },
            "reinvestmentPriors": {
                "industrySalesToCapital": capex.sales_to_capital if capex else None,
                "industryNetCapexToSales": capex.net_capex_to_sales if capex else None,
                "industryWorkingCapitalToSales": wc.non_cash_wc_to_sales if wc else None,
                "suggestedSalesToCapital": capex.sales_to_capital if capex else None
            },
            "returnPriors": {
                "industryRoc": roe.roc if roe else None,
                "industryRoe": roe.roe if roe else None,
                "industryRoeAdjustedForRd": roe.rd_adjusted_roe if roe else None,
                "suggestedTerminalRoc": roe.roc if roe else None
            },
            "capitalStructurePriors": {
                "currentDebtRatio": None,
                "industryDebtSignals": None,
                "regressionImpliedDebtRatio": None,
                "suggestedTargetDebtRatio": None
            },
            "financingFlowPriors": {
                "numberOfFirms": financing.number_of_firms if financing else None,
                "dividendsUsdMillions": financing.dividends_usd_millions if financing else None,
                "buybacksUsdMillions": financing.buybacks_usd_millions if financing else None,
                "equityIssuanceUsdMillions": financing.equity_issuance_usd_millions if financing else None,
                "debtRaisedUsdMillions": financing.debt_raised_usd_millions if financing else None,
                "debtRepaidUsdMillions": financing.debt_repaid_usd_millions if financing else None,
                "contextOnly": True,
            },
            "sourceSummary": source_summary,
        }

    @staticmethod
    def get_weighted_assumption_priors(
        db: Session,
        country: str,
        allocations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not allocations:
            raise ValueError("At least one industry allocation is required")
        weights = [item["weight_percent"] for item in allocations]
        if any(
            isinstance(weight, bool) or not isinstance(weight, (int, float))
            or not isfinite(weight) or not 0 < weight <= 100
            for weight in weights
        ):
            raise ValueError("Industry allocation weights must be finite and between 0% and 100%")
        total = fsum(weights)
        if abs(total - 100.0) > 0.01:
            raise ValueError("Industry allocation weights must total 100%")

        components = [
            {
                **allocation,
                # Normalize only the rounding allowed by the 100% total check.
                "weight_fraction": float(allocation["weight_percent"]) / total,
                "priors": IndustryAssumptionService.get_assumption_priors(
                    db,
                    country,
                    str(allocation["industry_name"]),
                ),
            }
            for allocation in allocations
        ]
        result = deepcopy(components[0]["priors"])
        result.update(
            {
                "country": country,
                "industry": "Revenue-weighted industry blend",
                "aggregationVersion": IndustryAssumptionService.WEIGHTED_PRIOR_VERSION,
                "dataVersion": {
                    "activeDatasetFileIds": sorted({
                        dataset_id
                        for component in components
                        for dataset_id in component["priors"].get("dataVersion", {}).get("activeDatasetFileIds", [])
                    })
                },
                "industryMix": [
                    {
                        "segmentName": component["segment_name"],
                        "industryName": component["industry_name"],
                        "weightPercent": component["weight_percent"],
                    }
                    for component in components
                ],
            }
        )

        fields = {
            "revenueGrowthPriors": (
                "industryHistorical5Y",
                "industryExpected2Y",
                "industryExpected5Y",
                "suggestedYears1To2",
                "suggestedYears3To5",
            ),
            "marginPriors": (
                "industryUnadjustedOperatingMargin",
                "industryLeaseAdjustedMargin",
                "industryLeaseRdAdjustedMargin",
                "suggestedTargetMargin",
            ),
            "reinvestmentPriors": (
                "industrySalesToCapital",
                "industryNetCapexToSales",
                "industryWorkingCapitalToSales",
                "suggestedSalesToCapital",
            ),
            "returnPriors": (
                "industryRoc", "industryRoe", "industryRoeAdjustedForRd", "suggestedTerminalRoc",
            ),
            "capitalStructurePriors": ("industryDebtSignals", "suggestedTargetDebtRatio"),
        }
        warnings: list[str] = []
        coverage: dict[str, dict[str, bool]] = {}
        methods: dict[str, dict[str, str]] = {}
        multiple_industries = len({
            str(item["industry_name"]).strip().casefold() for item in allocations
        }) > 1
        capital_ratios = {"industrySalesToCapital", "suggestedSalesToCapital"}
        for group, keys in fields.items():
            coverage[group] = {}
            methods[group] = {}
            for key in keys:
                values = [component["priors"].get(group, {}).get(key) for component in components]
                valid = [
                    isinstance(value, (int, float)) and not isinstance(value, bool)
                    and isfinite(value) and (key not in capital_ratios or value > 0)
                    for value in values
                ]
                if multiple_industries and group in {"returnPriors", "capitalStructurePriors"}:
                    result[group][key] = None
                    coverage[group][key] = False
                    methods[group][key] = "unavailable_without_denominator_weights"
                    warnings.append(
                        f"{group}.{key} is unavailable: revenue weights do not establish "
                        "capital or equity weights for this ratio."
                    )
                    continue
                if multiple_industries and group == "revenueGrowthPriors":
                    result[group][key] = None
                    coverage[group][key] = False
                    methods[group][key] = "unavailable_without_growth_period_basis"
                    warnings.append(
                        f"{group}.{key} is unavailable: multi-year growth requires matched "
                        "base periods and compounding, not an arithmetic average of rates."
                    )
                    continue
                if not all(valid):
                    result[group][key] = None
                    coverage[group][key] = False
                    methods[group][key] = "unavailable_component"
                    missing = [
                        component["segment_name"]
                        for usable, component in zip(valid, components, strict=True)
                        if not usable
                    ]
                    warnings.append(
                        f"{group}.{key} is unavailable because benchmark data is missing or invalid for: "
                        + ", ".join(missing)
                    )
                    continue
                try:
                    if key in capital_ratios:
                        # Capital_i = Revenue_i / (Sales/Capital)_i. Sum capital
                        # before dividing total revenue, rather than averaging ratios.
                        blended = 1.0 / fsum(
                            component["weight_fraction"] / float(value)
                            for value, component in zip(values, components, strict=True)
                        )
                        method = "revenue_weighted_harmonic_ratio"
                    else:
                        blended = fsum(
                            float(value) * component["weight_fraction"]
                            for value, component in zip(values, components, strict=True)
                        )
                        method = "revenue_weighted_mean" if multiple_industries else "single_industry_prior"
                except (OverflowError, ZeroDivisionError):
                    blended = float("nan")
                    method = "unavailable_numeric_range"
                usable = isfinite(blended) and (key not in capital_ratios or blended > 0)
                result[group][key] = blended if usable else None
                coverage[group][key] = usable
                methods[group][key] = method if usable else "unavailable_numeric_range"
                if not usable:
                    warnings.append(f"{group}.{key} is unavailable outside the supported numeric range.")

        if multiple_industries:
            # These are absolute totals for an industry's constituent companies,
            # not ratios or the first segment's contribution to this company.
            result["financingFlowPriors"] = {
                key: True if key == "contextOnly" else None
                for key in result.get("financingFlowPriors", {})
            }
            warnings.append(
                "Financing-flow industry totals are unavailable for a revenue-weighted blend; "
                "inspect each industry's context separately."
            )

        result["coverage"] = coverage
        result["aggregationMethods"] = methods
        result["warnings"] = warnings
        result["sourceSummary"] = [
            {
                "segmentName": component["segment_name"],
                "industryName": component["industry_name"],
                "weightPercent": component["weight_percent"],
                "sources": component["priors"]["sourceSummary"],
            }
            for component in components
        ]
        return result
