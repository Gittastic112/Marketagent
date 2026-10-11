from dataclasses import dataclass
from math import fsum, isfinite
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import CountryMarketStats, DamodaranPricingBenchmark
from app.services.peer_valuation_sets import (
    PeerValuationSetService,
    calculate_peer_diagnostics,
    calculate_peer_aggregates,
    peer_set_members,
    peer_set_calculation_eligibility,
    peer_set_response,
    peer_set_target_context,
)


PRICING_SOURCE_CODES = ("pe", "pbv", "ps", "vebitda")


class FinancialsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None
    netIncome: Optional[float] = None
    bookEquity: Optional[float] = None
    investedCapital: Optional[float] = None
    debt: Optional[float] = Field(default=None, ge=0)
    cash: Optional[float] = Field(default=None, ge=0)
    dilutedShares: Optional[float] = Field(default=None, gt=0)

    @field_validator("*", mode="before")
    @classmethod
    def reject_boolean_financials(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("Financial inputs must be numbers, not booleans")
        return value


class RelativeValuationBasis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    country: Optional[str] = Field(default=None, min_length=1, max_length=120)
    industryName: Optional[str] = Field(default=None, min_length=1, max_length=255)
    peerSetId: Optional[int] = Field(default=None, ge=1, le=2_147_483_647, strict=True)
    methods: list[Literal["pe", "pbv", "ps", "ev_sales", "ev_ebitda", "ev_ebit"]] = Field(min_length=1, max_length=6)

    @field_validator("methods")
    @classmethod
    def require_unique_methods(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("Select each valuation method only once")
        return value

    @model_validator(mode="after")
    def require_one_benchmark(self) -> "RelativeValuationBasis":
        if self.peerSetId is not None and (self.country is not None or self.industryName is not None):
            raise ValueError("Choose either a peer set or a country/industry benchmark, not both")
        if self.peerSetId is None and (not self.country or not self.industryName):
            raise ValueError("Country and industry are required without a reviewed peer set")
        return self


class RelativeValuationRequest(RelativeValuationBasis):
    companyId: Optional[str] = None
    financials: FinancialsInput

    @field_validator("companyId")
    @classmethod
    def validate_company_id(cls, value: str | None) -> str | None:
        if value is not None:
            if not value.isascii() or not value.isdecimal() or len(value) > 10 or not 1 <= int(value) <= 2_147_483_647:
                raise ValueError("Company ID must be a positive database identifier")
            return str(int(value))
        return value


class SavedRelativeValuationRequest(RelativeValuationBasis):
    confirmInputBasis: bool = Field(strict=True)
    inputBasisSha256: str = Field(pattern=r"^[a-f0-9]{64}$")


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
    def run_valuation(
        db: Session,
        req: RelativeValuationRequest,
        *,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        peer_set = None
        peer_aggregates = None
        peer_diagnostics = None
        benchmark = None
        if req.peerSetId is not None:
            if user_id is None:
                return {"error": "Authenticated owner is required for peer-set valuation"}
            peer_set = PeerValuationSetService.get_set(
                db,
                peer_set_id=req.peerSetId,
                user_id=user_id,
            )
            if req.companyId is not None:
                try:
                    requested_company_id = int(req.companyId)
                except ValueError:
                    return {"error": "Company ID must be an integer for peer-set valuation"}
                if requested_company_id != peer_set.company_id:
                    return {"error": "Peer valuation set does not belong to the requested company"}
            peer_members = peer_set_members(peer_set)
            target_context = peer_set_target_context(peer_set)
            peer_aggregates = calculate_peer_aggregates(peer_members)
            peer_diagnostics = calculate_peer_diagnostics(
                peer_members,
                target_context=target_context,
            )
            eligibility = peer_set_calculation_eligibility(peer_set, diagnostics=peer_diagnostics)
            receipt_error = "Peer valuation set diagnostics acknowledgement is missing or stale; review the current warnings before use"
            blocking_messages = {
                "archived": "Peer valuation set is archived",
                "review_required": "Peer valuation set must be reviewed before use",
                "member_storage_mismatch": "Peer member storage mismatch must be repaired before valuation use",
                "target_storage_mismatch": "Target profile storage mismatch must be repaired before valuation use",
                "receipt_missing": receipt_error,
                "receipt_stale": receipt_error,
            }
            for blocker in eligibility["blockers"]:
                if blocker in blocking_messages:
                    return {"error": blocking_messages[blocker]}
            # Sparse methods retain the existing per-method unavailable response below.
        else:
            benchmark = RelativeValuationBenchmarkService.get_industry_benchmark(
                db, req.country or "", req.industryName or ""
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
            source_row = benchmark.row(source_code) if benchmark is not None else None
            source: dict[str, Any] | None
            reliability: str
            if peer_set is not None:
                method_aggregate = (peer_aggregates or {}).get("methods", {}).get(method_id)
                multiple = method_aggregate.get("multiple") if method_aggregate else None
                source = PeerValuationSetService.method_source(peer_set, method_id)
                if multiple is None or source is None:
                    eligible_count = method_aggregate.get("eligibleCount", 0) if method_aggregate else 0
                    unavailable_methods.append(
                        {
                            "method": method_id,
                            "reason": (
                                f"Reviewed peer set has {eligible_count} eligible value(s); "
                                "at least 3 are required"
                            ),
                        }
                    )
                    return
                reliability = "low" if source["warnings"] else "medium"
            else:
                source = benchmark.provenance(source_code) if benchmark is not None else None
                if source_row is None or multiple is None or source is None:
                    unavailable_methods.append(
                        {"method": method_id, "reason": f"Active {source_code} benchmark is unavailable"}
                    )
                    return
                reliability = RelativeValuationBenchmarkService.calculate_reliability(
                    source_row.number_of_firms, pct_money_losing, multiple
                )
            if base_value is None or base_value <= 0:
                unavailable_methods.append(
                    {"method": method_id, "reason": "Required positive company financial is unavailable"}
                )
                return
            enterprise_value = base_value * multiple if enterprise_multiple else None
            equity_value = to_equity_value(enterprise_value) if enterprise_multiple else base_value * multiple
            value_per_share = to_per_share(equity_value)
            if any(value is not None and not isfinite(value) for value in (
                multiple, enterprise_value, equity_value, value_per_share,
            )):
                unavailable_methods.append({
                    "method": method_id,
                    "reason": "Calculation exceeds the supported numeric range; check input units and share count",
                })
                return
            result = {
                "method": label,
                "methodId": method_id,
                "benchmarkMultiple": multiple,
                "enterpriseValue": enterprise_value,
                "equityValue": equity_value,
                "valuePerShare": value_per_share,
                "reliability": reliability,
                "claimType": "Calculation",
                "source": source,
            }
            results.append(result)
            if value_per_share is not None:
                implied_prices.append(value_per_share)

        pe = benchmark.row("pe") if benchmark is not None else None
        pbv = benchmark.row("pbv") if benchmark is not None else None
        ps = benchmark.row("ps") if benchmark is not None else None
        ev = benchmark.row("vebitda") if benchmark is not None else None

        if peer_set is not None:
            diagnostics.append(
                f"Reviewed peer set '{peer_set.name}' uses the median of at least 3 positive included peer multiples."
            )
            diagnostics.extend(
                warning["message"]
                for warning in (peer_diagnostics or {}).get("warnings", [])
                if warning.get("method") in (None, *req.methods)
            )

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
            scale = max(abs(value) for value in implied_prices)
            value_range = {
                "low": implied_prices[0],
                # Normalize before summation to keep even near-limit means finite.
                "base": (fsum(value / scale for value in implied_prices) / len(implied_prices)) * scale if scale else 0.0,
                "high": implied_prices[-1],
            }

        return {
            "benchmarkType": "reviewed_peer_set" if peer_set is not None else "industry_aggregate",
            "industryName": benchmark.industry_name if benchmark is not None else None,
            "peerSet": peer_set_response(peer_set, include_members=False) if peer_set is not None else None,
            "relativeValues": results,
            "range": value_range,
            "diagnostics": diagnostics,
            "unavailableMethods": unavailable_methods,
            "benchmarkSources": (
                [
                    benchmark.sources[code].provenance()
                    for code in PRICING_SOURCE_CODES
                    if code in benchmark.sources
                ]
                if benchmark is not None
                else []
            ),
        }
