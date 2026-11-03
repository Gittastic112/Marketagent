"""Public contracts for the owned source-refresh queue and its fixed local schedule."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ValuationSourceRefreshRead(BaseModel):
    id: int
    company_id: int | None = None
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    scheduled_for: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    draft_ids: list[int] = Field(default_factory=list)


class ValuationRefreshStatusRead(BaseModel):
    enabled: bool
    timezone: str
    local_time: str
    weekdays: list[int]
    next_scheduled_at: datetime | None = None
    latest_run: ValuationSourceRefreshRead | None = None
    policy: str
    runtime_requirement: str
