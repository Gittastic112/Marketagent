"""Companies API contracts, independent of HTTP and persistence."""

from datetime import (
    date,
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from typing import (
    Literal,
)


class ExposureTagCreate(BaseModel):
    name: str
    description: str | None = None


class ExposureTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None


class CompanyCreate(BaseModel):
    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    damodaran_industry: str | None = None
    exchange: str | None = None
    market: str | None = None
    primary_exchange: str | None = None
    local_symbol: str | None = None
    isin: str | None = None
    figi: str | None = None
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    cik: str | None = None
    aliases_json: list[str] | None = None
    country: str | None = None
    region: str | None = None
    currency: str | None = None
    asset_type: str | None = None
    security_type: str | None = None
    market_cap_category: str | None = None
    is_etf: bool = False
    etf_provider: str | None = None
    active: bool = True


class CompanyUpdate(BaseModel):
    ticker: str | None = None
    name: str | None = None
    sector: str | None = None
    industry: str | None = None
    damodaran_industry: str | None = None
    exchange: str | None = None
    market: str | None = None
    primary_exchange: str | None = None
    local_symbol: str | None = None
    isin: str | None = None
    figi: str | None = None
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    cik: str | None = None
    aliases_json: list[str] | None = None
    country: str | None = None
    region: str | None = None
    currency: str | None = None
    asset_type: str | None = None
    security_type: str | None = None
    market_cap_category: str | None = None
    is_etf: bool | None = None
    etf_provider: str | None = None
    active: bool | None = None


class CompanyRead(CompanyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    exposure_tags: list[ExposureTagRead] = []


class IndustryMappingUpdate(BaseModel):
    industry_name: str


class IndustryAllocationInput(BaseModel):
    segment_name: str = Field(min_length=1, max_length=120)
    industry_name: str = Field(min_length=1, max_length=255)
    weight_percent: float = Field(gt=0, le=100)


class CompanyIndustryMixUpdate(BaseModel):
    basis: Literal["revenue"] = "revenue"
    as_of_date: date | None = None
    source_document_id: int | None = None
    notes: str | None = Field(default=None, max_length=1000)
    allocations: list[IndustryAllocationInput] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_mix(self):
        labels = [allocation.segment_name.strip().casefold() for allocation in self.allocations]
        if len(labels) != len(set(labels)):
            raise ValueError("Segment labels must be unique")
        total = sum(allocation.weight_percent for allocation in self.allocations)
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Industry weights must total 100%; received {total:.4f}%")
        return self


class IndustryAllocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    segment_name: str
    industry_name: str
    weight_percent: float
    benchmark_availability: dict[str, bool] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class CompanyIndustryMixRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    basis: str
    as_of_date: date | None
    source_document_id: int | None
    notes: str | None
    primary_industry: str
    total_weight_percent: float
    claim_type: Literal["User Assumption"] = "User Assumption"
    coverage_status: Literal["complete", "partial", "unavailable"]
    benchmark_field_coverage: dict[str, dict[str, bool]]
    warnings: list[str] = Field(default_factory=list)
    allocations: list[IndustryAllocationRead]
    created_at: datetime
    updated_at: datetime


class CompanyLookupRead(BaseModel):
    market: str
    primary_exchange: str | None = None
    ticker: str
    local_symbol: str
    name: str
    currency: str
    country: str
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    cik: str | None = None
    isin: str | None = None
    source: str
    warnings: list[str] = Field(default_factory=list)


class CompanySetupStartRequest(BaseModel):
    company_id: int


class CompanySetupStepUpdate(BaseModel):
    current_step: str | None = None
    identity_status: str | None = None
    source_status: str | None = None
    filing_status: str | None = None
    financial_extraction_status: str | None = None
    industry_mapping_status: str | None = None
    valuation_readiness_status: str | None = None
    security_review_status: str | None = None


class CompanySetupSourceReadiness(BaseModel):
    provider_name: str
    capability: str
    market: str
    status: str
    notes: str
    action_required: str | None = None


class CompanySetupIdentityResolution(BaseModel):
    company_id: int
    market: str
    ticker: str
    local_symbol: str | None = None
    primary_exchange: str | None = None
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    cik: str | None = None
    confidence_label: str
    missing_identifiers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CompanySetupWorkflowRead(BaseModel):
    id: int
    company_id: int
    current_step: str
    identity_status: str
    source_status: str
    filing_status: str
    financial_extraction_status: str
    industry_mapping_status: str
    valuation_readiness_status: str
    security_review_status: str
    source_readiness: list[CompanySetupSourceReadiness] = Field(default_factory=list)
    next_recommended_step: str
    created_at: datetime
    updated_at: datetime
