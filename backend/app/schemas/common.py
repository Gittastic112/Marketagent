"""Shared API envelope contracts, independent of HTTP, services and persistence.

The legacy app.api.schemas module re-exports these exact classes for compatibility.
"""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiMeta(BaseModel):
    status: str = "success"
    last_updated: datetime | None = None
    source: str = "internal"
    is_stale: bool = False
    is_mock: bool = False
    warnings: list[str] = Field(default_factory=list)
    confidence: str = "medium"
    processing_time_ms: int | None = None
    request_id: str | None = None


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    target: str | None = None
    retryable: bool = False
    field: str | None = None
    provider: str | None = None
    processing_run_id: int | None = None


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    data: T | None = None
    meta: ApiMeta = Field(default_factory=ApiMeta)
    errors: list[ApiErrorDetail] = Field(default_factory=list)
