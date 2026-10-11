from copy import deepcopy
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
        total = sum(float(item["weight_percent"]) for item in allocations)
        if abs(total - 100.0) > 0.01:
            raise ValueError("Industry allocation weights must total 100%")

        components = [
            {
                **allocation,
                "weight_fraction": float(allocation["weight_percent"]) / 100.0,
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
            "returnPriors": ("industryRoc", "industryRoe", "suggestedTerminalRoc"),
            "capitalStructurePriors": ("industryDebtSignals", "suggestedTargetDebtRatio"),
        }
        warnings: list[str] = []
        coverage: dict[str, dict[str, bool]] = {}
        for group, keys in fields.items():
            coverage[group] = {}
            for key in keys:
                values = [component["priors"].get(group, {}).get(key) for component in components]
                complete = all(isinstance(value, (int, float)) for value in values)
                coverage[group][key] = complete
                if complete:
                    result[group][key] = sum(
                        float(value) * component["weight_fraction"]
                        for value, component in zip(values, components, strict=True)
                    )
                else:
                    result[group][key] = None
                    missing = [
                        component["segment_name"]
                        for value, component in zip(values, components, strict=True)
                        if not isinstance(value, (int, float))
                    ]
                    warnings.append(
                        f"{group}.{key} is unavailable because benchmark data is missing for: "
                        + ", ".join(missing)
                    )

        result["coverage"] = coverage
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
