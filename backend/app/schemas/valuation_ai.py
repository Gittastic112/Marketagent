"""Saved-basis requests and bounded optional valuation interpretations."""
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ValuationAIRequest(BaseModel):
    privacy_disclosure_version: str
    # Optional for legacy callers. The application always supplies both fields.
    assumption_set_id: int | None = Field(default=None, gt=0)
    assumptions_updated_at: datetime | None = None

    @model_validator(mode="after")
    def complete_basis(self):
        if (self.assumption_set_id is None) != (self.assumptions_updated_at is None):
            raise ValueError("Supply both the saved assumption ID and its update time.")
        return self


class NarrativeRequest(ValuationAIRequest):
    narrative_text: str = Field(min_length=1, max_length=20000)


class NarrativeEstimates(BaseModel):
    """Provider estimates stay untrusted until their complete shape is checked."""

    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)

    target_operating_margin: float = Field(ge=-1, le=1)
    target_operating_margin_reason: str = Field(min_length=1, max_length=2000)
    revenue_growth_years: dict[
        Annotated[str, Field(pattern=r"^(?:[1-9]|[12][0-9]|30)$")],
        Annotated[float, Field(ge=-0.99, le=5)],
    ] = Field(min_length=1, max_length=30)
    revenue_growth_reason: str = Field(min_length=1, max_length=2000)
    sales_to_capital_ratio: float = Field(gt=0)
    sales_to_capital_reason: str = Field(min_length=1, max_length=2000)
    terminal_growth_rate: float = Field(ge=-0.99, le=0.99)
    terminal_growth_reason: str = Field(min_length=1, max_length=2000)
