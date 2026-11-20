from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OriginalSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["raw_document"]
    id: int = Field(gt=0)
    revision_id: int | None = Field(default=None, gt=0)
    event_id: int | None = Field(default=None, gt=0)


class PriceDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    assumption_id: int = Field(gt=0)
    original: OriginalSelection | None = None
    valuation_version_id: int | None = Field(default=None, gt=0)
    decision: Literal["no_change", "propose_change", "blocked"]
    reason: str = Field(min_length=1, max_length=2000)


class PriceDecisionConfirm(PriceDecision):
    request_id: UUID
    context_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class PriceDecisionPreview(BaseModel):
    context_hash: str
    context: dict[str, Any]


class PriceDecisionSaved(BaseModel):
    change_id: int
    replayed: bool
