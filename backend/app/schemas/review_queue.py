from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ReviewQueueState = Literal["needs_review", "waiting_for_source", "in_progress", "new_source"]


class ReviewQueueItem(BaseModel):
    identity: str
    domain: str
    record_id: int
    company_id: int | None
    ticker: str | None
    title: str
    reason: str
    state: ReviewQueueState
    relevant_at: datetime
    href: str
    action: str
    permission_scope: Literal["owned", "shared_source"]
    severity_basis: str


class ReviewQueueRead(BaseModel):
    captured_at: datetime
    portfolio_id: int | None
    items: list[ReviewQueueItem]
    counts: dict[str, int]
    total: int
    returned: int
    limit: int
    truncated: bool
    basis: str
    limitations: list[str]
