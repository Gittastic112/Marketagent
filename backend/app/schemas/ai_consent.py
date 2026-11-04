"""Owner-scoped AI permission contracts, independent of HTTP and persistence."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ConsentState = Literal["granted", "refused", "revoked"]


class AIConsentDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_name: Literal["gemini"]
    action_key: str = Field(min_length=1, max_length=60)
    state: ConsentState
    disclosure_version: str = Field(min_length=1, max_length=50)
    scope_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_revision: int = Field(ge=0)


class AIConsentDecisionRead(BaseModel):
    id: int
    provider_name: str
    action_key: str
    revision: int
    state: ConsentState
    disclosure_version: str
    scope_hash: str
    external_data_classes: list[str]
    created_at: datetime


class AIConsentActionRead(BaseModel):
    provider_name: Literal["gemini"]
    action_key: str
    label: str
    description: str
    external_data_classes: list[str]
    disclosure_version: str
    scope_hash: str
    state: Literal["not_granted", "granted", "refused", "revoked", "outdated"]
    current_revision: int
    latest_decision: AIConsentDecisionRead | None


class AIConsentOverview(BaseModel):
    actions: list[AIConsentActionRead]
    limitations: list[str]


class AIConsentHistory(BaseModel):
    items: list[AIConsentDecisionRead]
    next_cursor: int | None
