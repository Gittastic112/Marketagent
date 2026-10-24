import difflib
import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.company_industry import CompanyIndustryAllocation, CompanyIndustryMix
from app.models.company_setup import CompanySetupWorkflow
from app.models.damodaran_fundamentals import (
    CountryMarketStats,
    DamodaranCapexBenchmark,
    DamodaranDividendBenchmark,
    DamodaranGrowthBenchmark,
    DamodaranMarginBenchmark,
    DamodaranPricingBenchmark,
    DamodaranRoeBenchmark,
    DamodaranWcBenchmark,
)
from app.models.real_options import IndustryVolatilityBenchmark
from app.models.raw_document import RawDocument
from app.services.damodaran_dataset_versions import active_dataset_ids


def _profile_tokens(value: str) -> set[str]:
    # Broad sector words do not establish a specific business comparison.
    # Keep "non-bank" distinct from bank before splitting punctuation.
    value = re.sub(r"non[\s-]*bank", "nonbank", value.casefold())
    generic = {"and", "other", "general", "diversified", "business", "consumer",
               "service", "services", "technology", "information", "product",
               "products", "industry", "industries"}
    aliases = {"banks": "bank", "banking": "bank", "computers": "computer",
               "semiconductors": "semiconductor", "electronics": "electronic"}
    tokens = set(re.findall(r"[a-z]+", value)) - generic
    return {"transport" if token.startswith("transport") else aliases.get(token, token) for token in tokens}


def _shares_profile_token(left: str, right: str) -> bool:
    return bool(_profile_tokens(left) & _profile_tokens(right))

class IndustryMappingService:
    @staticmethod
    def get_available_industries(
        db: Session,
        country: str = "India",
        *,
        fallback_to_loaded: bool = True,
    ) -> list[str]:
        stmt = (
            select(DamodaranMarginBenchmark.industry_name)
            .where(
                DamodaranMarginBenchmark.country == country,
                DamodaranMarginBenchmark.dataset_file_id.in_(active_dataset_ids()),
            )
            .distinct()
        )
        results = list(db.scalars(stmt))
        if not results and fallback_to_loaded:
            results = list(
                db.scalars(
                    select(DamodaranMarginBenchmark.industry_name)
                    .where(DamodaranMarginBenchmark.dataset_file_id.in_(active_dataset_ids()))
                    .distinct()
                )
            )
        return sorted({result for result in results if result})

    @staticmethod
    def get_available_countries(db: Session) -> list[str]:
        return sorted(
            {
                country
                for country in db.scalars(
                    select(DamodaranMarginBenchmark.country)
                    .where(DamodaranMarginBenchmark.dataset_file_id.in_(active_dataset_ids()))
                    .distinct()
                )
                if country
            }
        )

    @staticmethod
    def suggest_damodaran_industries(db: Session, company_id: int, country: str = "India") -> list[dict[str, Any]]:
        company = db.get(Company, company_id)

        all_industries = IndustryMappingService.get_available_industries(
            db, country, fallback_to_loaded=False,
        )

        candidates = []
        if company:
            search_terms = []
            if company.industry and _profile_tokens(company.industry):
                search_terms.append(company.industry.strip().lower())

            # Require a shared profile token so permissive edit distance cannot
            # suggest unrelated industries with similar suffixes.
            for term in search_terms:
                matches = sorted(
                    (
                        (difflib.SequenceMatcher(None, term, industry.casefold()).ratio(), industry)
                        for industry in all_industries
                        if _shares_profile_token(term, industry)
                    ),
                    reverse=True,
                )[:3]
                for score, original_ind in matches:
                    if original_ind not in [c["industryName"] for c in candidates]:
                        candidates.append({
                            "industryName": original_ind,
                            "confidence": "medium",
                            "reason": f"Text match to company industry: {term.title()}. Review the comparison before use."
                        })

        for c in candidates:
            c["benchmarkAvailability"] = IndustryMappingService._benchmark_availability(
                db,
                country,
                c["industryName"],
            )

        return candidates

    @staticmethod
    def _benchmark_availability(db: Session, country: str, industry_name: str) -> dict[str, bool]:
        def has_industry(model: type) -> bool:
            stmt = select(model.id).where(
                model.country == country,
                model.industry_name == industry_name,
            )
            if hasattr(model, "dataset_file_id"):
                stmt = stmt.where(model.dataset_file_id.in_(active_dataset_ids()))
            return db.scalar(stmt.limit(1)) is not None

        return {
            "margins": has_industry(DamodaranMarginBenchmark),
            "capex": has_industry(DamodaranCapexBenchmark),
            "workingCapital": has_industry(DamodaranWcBenchmark),
            "returns": has_industry(DamodaranRoeBenchmark),
            "growth": has_industry(DamodaranGrowthBenchmark),
            "multiples": has_industry(DamodaranPricingBenchmark),
            "payout": has_industry(DamodaranDividendBenchmark),
            "macro": db.scalar(
                select(CountryMarketStats.id).where(
                    CountryMarketStats.country == country,
                    CountryMarketStats.dataset_file_id.in_(active_dataset_ids()),
                ).limit(1)
            ) is not None,
            "volatility": has_industry(IndustryVolatilityBenchmark),
        }

    @staticmethod
    def get_industry_mix(db: Session, company_id: int) -> CompanyIndustryMix | None:
        return db.scalar(
            select(CompanyIndustryMix).where(CompanyIndustryMix.company_id == company_id)
        )

    @staticmethod
    def serialize_industry_mix(db: Session, mix: CompanyIndustryMix) -> dict[str, Any]:
        company = db.get(Company, mix.company_id)
        country = (company.country if company else None) or "India"
        allocations = list(mix.allocations)
        primary = max(allocations, key=lambda allocation: allocation.weight_percent).industry_name
        serialized_allocations = [
            {
                "id": allocation.id,
                "segment_name": allocation.segment_name,
                "industry_name": allocation.industry_name,
                "weight_percent": allocation.weight_percent,
                "benchmark_availability": IndustryMappingService._benchmark_availability(
                    db,
                    country,
                    allocation.industry_name,
                ),
                "created_at": allocation.created_at,
                "updated_at": allocation.updated_at,
            }
            for allocation in allocations
        ]
        from app.services.industry_assumption import IndustryAssumptionService

        priors = IndustryAssumptionService.get_weighted_assumption_priors(
            db,
            country,
            [
                {
                    "segment_name": allocation.segment_name,
                    "industry_name": allocation.industry_name,
                    "weight_percent": allocation.weight_percent,
                }
                for allocation in allocations
            ],
        )
        field_coverage = priors.get("coverage", {})
        field_states = [state for group in field_coverage.values() for state in group.values()]
        coverage_status = (
            "unavailable"
            if not field_states or not any(field_states)
            else "complete" if all(field_states) else "partial"
        )
        return {
            "id": mix.id,
            "company_id": mix.company_id,
            "basis": mix.basis,
            "as_of_date": mix.as_of_date,
            "source_document_id": mix.source_document_id,
            "notes": mix.notes,
            "primary_industry": primary,
            "total_weight_percent": sum(allocation.weight_percent for allocation in allocations),
            "claim_type": "User Assumption",
            "coverage_status": coverage_status,
            "benchmark_field_coverage": field_coverage,
            "warnings": priors.get("warnings", []),
            "allocations": serialized_allocations,
            "created_at": mix.created_at,
            "updated_at": mix.updated_at,
        }

    @staticmethod
    def industry_mix_context(db: Session, company_id: int) -> dict[str, Any] | None:
        from app.services.industry_assumption import IndustryAssumptionService

        mix = IndustryMappingService.get_industry_mix(db, company_id)
        if mix is None or not mix.allocations:
            return None
        allocations = [
            {
                "segment_name": allocation.segment_name,
                "industry_name": allocation.industry_name,
                "weight_percent": allocation.weight_percent,
            }
            for allocation in mix.allocations
        ]
        signature_payload = {
            "aggregation_version": IndustryAssumptionService.WEIGHTED_PRIOR_VERSION,
            "basis": mix.basis,
            "as_of_date": mix.as_of_date.isoformat() if mix.as_of_date else None,
            "source_document_id": mix.source_document_id,
            "allocations": allocations,
        }
        return {
            **signature_payload,
            "mix_id": mix.id,
            "notes": mix.notes,
            "signature": hashlib.sha256(
                json.dumps(signature_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        }

    @staticmethod
    def save_industry_mix(
        db: Session,
        company_id: int,
        *,
        basis: str,
        allocations: list[dict[str, Any]],
        as_of_date=None,
        source_document_id: int | None = None,
        notes: str | None = None,
    ) -> CompanyIndustryMix:
        company = db.get(Company, company_id)
        if company is None:
            raise ValueError("Company not found")
        if basis != "revenue":
            raise ValueError("Only revenue-weighted industry mixes are currently supported")
        if not allocations:
            raise ValueError("At least one industry allocation is required")

        total = sum(float(item["weight_percent"]) for item in allocations)
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Industry weights must total 100%; received {total:.4f}%")
        segment_labels = [str(item["segment_name"]).strip().casefold() for item in allocations]
        if any(not label for label in segment_labels) or len(segment_labels) != len(set(segment_labels)):
            raise ValueError("Segment labels must be non-empty and unique")

        country = company.country or ("India" if (company.market or "").upper() == "IN" else "United States")
        available = IndustryMappingService.get_available_industries(
            db,
            country,
            fallback_to_loaded=False,
        )
        if not available:
            available = IndustryMappingService.get_available_industries(db, country)
        canonical_by_name = {candidate.casefold(): candidate for candidate in available}
        normalized: list[dict[str, Any]] = []
        for item in allocations:
            weight = float(item["weight_percent"])
            if weight <= 0 or weight > 100:
                raise ValueError("Industry weights must be greater than 0% and no more than 100%")
            requested = str(item["industry_name"]).strip()
            canonical = canonical_by_name.get(requested.casefold())
            if canonical is None:
                raise ValueError(f"Industry {requested!r} is not present in the loaded taxonomy")
            normalized.append(
                {
                    "segment_name": str(item["segment_name"]).strip(),
                    "industry_name": canonical,
                    "weight_percent": weight,
                }
            )

        if source_document_id is not None:
            source_document = db.get(RawDocument, source_document_id)
            if source_document is None or source_document.company_id != company_id:
                raise ValueError("Industry mix source document must belong to the company")

        mix = IndustryMappingService.get_industry_mix(db, company_id)
        if mix is None:
            mix = CompanyIndustryMix(company_id=company_id)
            db.add(mix)
            db.flush()
        else:
            mix.allocations.clear()
            db.flush()

        mix.basis = basis
        mix.as_of_date = as_of_date
        mix.source_document_id = source_document_id
        mix.notes = notes.strip() if notes and notes.strip() else None
        mix.updated_at = datetime.now(UTC)
        mix.allocations = [CompanyIndustryAllocation(**item) for item in normalized]

        primary = max(normalized, key=lambda item: item["weight_percent"])["industry_name"]
        company.damodaran_industry = primary
        workflow = db.scalar(
            select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company_id)
        )
        if workflow is not None:
            workflow.industry_mapping_status = "reviewed"
            if workflow.financial_extraction_status == "reviewed":
                workflow.current_step = "valuation_review"
        db.commit()
        db.refresh(mix)
        return mix

    @staticmethod
    def confirm_industry_mapping(db: Session, company_id: int, industry_name: str) -> Company:
        company = db.get(Company, company_id)
        if not company:
            raise ValueError("Company not found")

        IndustryMappingService.save_industry_mix(
            db,
            company_id,
            basis="revenue",
            allocations=[
                {
                    "segment_name": "Core operations",
                    "industry_name": industry_name,
                    "weight_percent": 100.0,
                }
            ],
        )
        db.refresh(company)
        return company
