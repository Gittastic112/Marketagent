from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PriceSeries(BaseModel):
    key: str
    provider: str
    symbol: str
    currency: str
    market: str | None
    exchange: str | None
    adjustment: str
    claim_type: str


class PriceAnchor(PriceSeries):
    price_id: int
    date: date
    price: str
    observed_at: datetime
    source_timestamp: datetime | None


class PricePinCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    thesis_id: int = Field(gt=0)
    price_id: int = Field(gt=0)
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    request_id: UUID
    text: str = Field(min_length=1, max_length=2000)


class PricePinRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    thesis_note_id: int
    anchor: PriceAnchor
    text: str
    created_at: datetime


class DatedSource(BaseModel):
    document_id: int
    title: str
    source: str
    context_date: date
    published: str
    sample: bool
    event_id: int | None = None
    summary: str | None = None


class PricePoint(BaseModel):
    date: date
    price: float | None = None
    price_id: int | None = None
    fingerprint: str | None = None
    previous_date: date | None = None
    change_pct: float | None = None
    large_move: bool = False
    gap_before: bool = False
    sources: list[DatedSource] = Field(default_factory=list)
    pins: list[PricePinRead] = Field(default_factory=list)


class PriceTimeline(BaseModel):
    series: PriceSeries | None = None
    choices: list[PriceSeries] = Field(default_factory=list)
    points: list[PricePoint] = Field(default_factory=list)
    move_threshold_pct: int = 5
    truncated: bool = False
    context_limited: bool = False
