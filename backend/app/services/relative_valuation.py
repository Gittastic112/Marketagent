from dataclasses import dataclass
from typing import Any, Literal, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import CountryMarketStats, DamodaranPricingBenchmark


PRICING_SOURCE_CODES = ("pe", "pbv", "ps", "vebitda")


class FinancialsInput(BaseModel):
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None
    netIncome: Optional[float] = None
    bookEquity: Optional[float] = None
    investedCapital: Optional[float] = None
    debt: Optional[float] = None
    cash: Optional[float] = None
    dilutedShares: Optional[float] = None


class RelativeValuationRequest(BaseModel):
    companyId: Optional[str] = None
    country: str
    industryName: str
    financials: FinancialsInput
    methods: list[Literal["pe", "pbv", "ps", "ev_sales", "ev_ebitda", "ev_ebit"]]


@dataclass(frozen=True, slots=True)
class PricingSource:
    code: str
    row: DamodaranPricingBenchmark
    version: DamodaranDatasetFile

    def provenance(self) -> dict[str, Any]:
        return {
            "sourceCode": self.code,
            "sourceFile": self.version.uploaded_filename,
            "datasetVersionId": self.version.id,
            "sourceSha256": self.version.source_sha256,
            "sourceAsOf": self.version.source_as_of,
            "dateConfidence": self.version.date_confidence,
            "canonicalSourcePath": self.version.canonical_source_path,
            "claimType": "Fact",
        }


@dataclass(frozen=True, slots=True)
class CountryMarketStatsBundle:
    row: CountryMarketStats
    version: DamodaranDatasetFile

    def provenance(self) -> dict[str, Any]:
        return {
            "sourceCode": "countrystats",
            "sourceFile": self.version.uploaded_filename,
            "datasetVersionId": self.version.id,
            "sourceSha256": self.version.source_sha256,
            "sourceAsOf": self.version.source_as_of,
            "dateConfidence": self.version.date_confidence,
            "canonicalSourcePath": self.version.canonical_source_path,
            "claimType": "Fact",
        }

    def as_dict(self) -> dict[str, Any]:
        data = {
            column.name: getattr(self.row, column.name)
            for column in CountryMarketStats.__table__.columns
            if column.name not in {"id", "dataset_file_id", "created_at"}
        }
        data["source"] = self.provenance()
        return data


@dataclass(frozen=True, slots=True)
class IndustryPricingBenchmark:
    country: str
    industry_name: str
    sources: dict[str, PricingSource]

    def row(self, source_code: str) -> DamodaranPricingBenchmark | None:
        source = self.sources.get(source_code)
        return source.row if source is not None else None

    def provenance(self, source_code: str) -> dict[str, Any] | None:
        source = self.sources.get(source_code)
        return source.provenance() if source is not None else None

    def as_dict(self) -> dict[str, Any]:
        metrics: dict[str, Any] = {}
        for source in self.sources.values():
            for column in DamodaranPricingBenchmark.__table__.columns:
                if column.name in {"id", "dataset_file_id", "created_at", "country", "industry_name"}:
                    continue
                value = getattr(source.row, column.name)
                if value is not None:
                    metrics[column.name] = value
        return {
            "country": self.country,
            "industryName": self.industry_name,
            "metrics": metrics,
            "sources": [
                self.sources[code].provenance()
                for code in PRICING_SOURCE_CODES
                if code in self.sources
            ],
        }


class RelativeValuationBenchmarkService:
    @staticmethod
    def get_countries(db: Session) -> list[str]:
        countries = [
            country
            for (country,) in (
                db.query(DamodaranPricingBenchmark.country)
                .join(
                    DamodaranDatasetFile,
                    DamodaranDatasetFile.id == DamodaranPricingBenchmark.dataset_file_id,
                )
                .filter(
                    DamodaranDatasetFile.is_active.is_(True),
                    DamodaranDatasetFile.dataset_code.in_(PRICING_SOURCE_CODES),
                    DamodaranPricingBenchmark.country.is_not(None),
                )
                .distinct()
                .order_by(DamodaranPricingBenchmark.country)
                .all()
            )
        ]
        if countries:
            return countries
        return [
            country
            for (country,) in db.query(CountryMarketStats.country)
            .join(
                DamodaranDatasetFile,
                DamodaranDatasetFile.id == CountryMarketStats.dataset_file_id,
            )
            .filter(
                DamodaranDatasetFile.dataset_code == "countrystats",
                DamodaranDatasetFile.is_active.is_(True),
            )
            .distinct()
            .order_by(CountryMarketStats.country)
            .all()
        ]

    @staticmethod
    def get_country_stats(
        db: Session,
        country: str,
    ) -> CountryMarketStatsBundle | None:
        match = (
            db.query(CountryMarketStats, DamodaranDatasetFile)
            .join(
                DamodaranDatasetFile,
                DamodaranDatasetFile.id == CountryMarketStats.dataset_file_id,
            )
            .filter(
                CountryMarketStats.country == country,
                DamodaranDatasetFile.dataset_code == "countrystats",
                DamodaranDatasetFile.is_active.is_(True),
            )
            .order_by(DamodaranDatasetFile.id.desc())
            .first()
        )
        if match is None:
            return None
        row, version = match
        return CountryMarketStatsBundle(row=row, version=version)

    @staticmethod
    def get_industries(db: Session, country: str) -> list[str]:
        return [
            industry
            for (industry,) in (
                db.query(DamodaranPricingBenchmark.industry_name)
                .join(
                    DamodaranDatasetFile,
                    DamodaranDatasetFile.id == DamodaranPricingBenchmark.dataset_file_id,
                )
                .filter(
                    DamodaranPricingBenchmark.country == country,
                    DamodaranDatasetFile.is_active.is_(True),
                    DamodaranDatasetFile.dataset_code.in_(PRICING_SOURCE_CODES),
                )
                .distinct()
                .order_by(DamodaranPricingBenchmark.industry_name)
                .all()
            )
        ]

    @staticmethod
    def get_industry_benchmark(
        db: Session,
        country: str,
        industry: str,
    ) -> IndustryPricingBenchmark | None:
        matches = (
            db.query(DamodaranPricingBenchmark, DamodaranDatasetFile)
            .join(
                DamodaranDatasetFile,
                DamodaranDatasetFile.id == DamodaranPricingBenchmark.dataset_file_id,
            )
            .filter(
                DamodaranPricingBenchmark.country == country,
                DamodaranPricingBenchmark.industry_name == industry,
                DamodaranDatasetFile.is_active.is_(True),
                DamodaranDatasetFile.dataset_code.in_(PRICING_SOURCE_CODES),
            )
            .order_by(DamodaranDatasetFile.id.desc())
            .all()
        )
        sources: dict[str, PricingSource] = {}
        for row, version in matches:
            sources.setdefault(
                version.dataset_code,
                PricingSource(code=version.dataset_code, row=row, version=version),
            )
        if not sources:
            return None
        return IndustryPricingBenchmark(
            country=country,
            industry_name=industry,
            sources=sources,
        )

    @staticmethod
    def calculate_reliability(
        num_firms: Optional[int],
        pct_money_losing: Optional[float],
        value: Optional[float],
    ) -> str:
        if value is None:
            return "not_applicable"

        score = 3
        if num_firms is not None and num_firms < 10:
            score -= 1
        if pct_money_losing is not None and pct_money_losing > 0.4:
            score -= 1
        if score >= 3:
            return "high"
        if score == 2:
            return "medium"
        return "low"


class RelativeValuationRunService:
    @staticmethod
    def run_valuation(db: Session, req: RelativeValuationRequest) -> dict[str, Any]:
        benchmark = RelativeValuationBenchmarkService.get_industry_benchmark(
            db, req.country, req.industryName
        )
        if not benchmark:
            return {"error": "Benchmark not found for the given country and industry"}

        results: list[dict[str, Any]] = []
        implied_prices: list[float] = []
        diagnostics: list[str] = []
        unavailable_methods: list[dict[str, str]] = []
        fin = req.financials

        def to_equity_value(ev: float) -> Optional[float]:
            if fin.debt is None or fin.cash is None:
                return None
            return ev - fin.debt + fin.cash

        def to_per_share(eq: Optional[float]) -> Optional[float]:
            if eq is None or not fin.dilutedShares or fin.dilutedShares <= 0:
                return None
            return eq / fin.dilutedShares

        def add_result(
            *,
            method_id: str,
            label: str,
            source_code: str,
            multiple: float | None,
            base_value: float | None,
            enterprise_multiple: bool,
            pct_money_losing: float | None = None,
        ) -> None:
            source_row = benchmark.row(source_code)
            if source_row is None or multiple is None:
                unavailable_methods.append(
                    {"method": method_id, "reason": f"Active {source_code} benchmark is unavailable"}
                )
                return
            if base_value is None or base_value <= 0:
                unavailable_methods.append(
                    {"method": method_id, "reason": "Required positive company financial is unavailable"}
                )
                return
            enterprise_value = base_value * multiple if enterprise_multiple else None
            equity_value = to_equity_value(enterprise_value) if enterprise_multiple else base_value * multiple
            value_per_share = to_per_share(equity_value)
            result = {
                "method": label,
                "methodId": method_id,
                "benchmarkMultiple": multiple,
                "enterpriseValue": enterprise_value,
                "equityValue": equity_value,
                "valuePerShare": value_per_share,
                "reliability": RelativeValuationBenchmarkService.calculate_reliability(
                    source_row.number_of_firms, pct_money_losing, multiple
                ),
                "claimType": "Calculation",
                "source": benchmark.provenance(source_code),
            }
            results.append(result)
            if value_per_share is not None:
                implied_prices.append(value_per_share)

        pe = benchmark.row("pe")
        pbv = benchmark.row("pbv")
        ps = benchmark.row("ps")
        ev = benchmark.row("vebitda")

        if "pe" in req.methods:
            add_result(
                method_id="pe",
                label="PE",
                source_code="pe",
                multiple=pe.pe_current if pe else None,
                base_value=fin.netIncome,
                enterprise_multiple=False,
                pct_money_losing=pe.percent_money_losing if pe else None,
            )
            if pe and pe.percent_money_losing is not None and pe.percent_money_losing > 0.3:
                diagnostics.append(
                    f"PE benchmark reliability is reduced because {pe.percent_money_losing * 100:.0f}% "
                    "of firms in the industry are money-losing."
                )
        if "pbv" in req.methods:
            add_result(
                method_id="pbv",
                label="PBV",
                source_code="pbv",
                multiple=pbv.pbv_ratio if pbv else None,
                base_value=fin.bookEquity,
                enterprise_multiple=False,
            )
        if "ps" in req.methods:
            add_result(
                method_id="ps",
                label="P/S",
                source_code="ps",
                multiple=ps.ps_ratio if ps else None,
                base_value=fin.revenue,
                enterprise_multiple=False,
            )
        if "ev_sales" in req.methods:
            add_result(
                method_id="ev_sales",
                label="EV/Sales",
                source_code="ps",
                multiple=ps.ev_to_sales if ps else None,
                base_value=fin.revenue,
                enterprise_multiple=True,
            )
        if "ev_ebitda" in req.methods:
            ev_ebitda_multiple = None
            if ev is not None:
                ev_ebitda_multiple = (
                    ev.ev_to_ebitda_positive_ebitda
                    if ev.ev_to_ebitda_positive_ebitda is not None
                    else ev.ev_to_ebitda_all
                )
            add_result(
                method_id="ev_ebitda",
                label="EV/EBITDA",
                source_code="vebitda",
                multiple=ev_ebitda_multiple,
                base_value=fin.ebitda,
                enterprise_multiple=True,
            )
        if "ev_ebit" in req.methods:
            ev_ebit_multiple = None
            if ev is not None:
                ev_ebit_multiple = (
                    ev.ev_to_ebit_positive_ebitda
                    if ev.ev_to_ebit_positive_ebitda is not None
                    else ev.ev_to_ebit_all
                )
            add_result(
                method_id="ev_ebit",
                label="EV/EBIT",
                source_code="vebitda",
                multiple=ev_ebit_multiple,
                base_value=fin.ebit,
                enterprise_multiple=True,
            )

        value_range = None
        if implied_prices:
            implied_prices.sort()
            value_range = {
                "low": implied_prices[0],
                "base": sum(implied_prices) / len(implied_prices),
                "high": implied_prices[-1],
            }

        return {
            "industryName": benchmark.industry_name,
            "relativeValues": results,
            "range": value_range,
            "diagnostics": diagnostics,
            "unavailableMethods": unavailable_methods,
            "benchmarkSources": [
                benchmark.sources[code].provenance()
                for code in PRICING_SOURCE_CODES
                if code in benchmark.sources
            ],
        }
