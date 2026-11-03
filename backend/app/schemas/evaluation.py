from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator


class ExpectedFinancialMetric(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    metric_code: str = Field(min_length=1, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    value: FiniteFloat
    unit: str = Field(min_length=1, max_length=80)
    fiscal_year: int = Field(ge=1900, le=2100)
    period_type: Literal["annual", "quarterly"]
    source_line_number: int = Field(ge=1, le=100_000)


class FinancialEvaluationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    run_name: str = Field(min_length=1, max_length=200)
    document_id: int = Field(gt=0)
    source_text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reference_reviewed: Literal[True]
    reference_is_complete: Literal[True]
    is_mock: bool
    expected: list[ExpectedFinancialMetric] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def unique_reference_rows(self):
        keys = [(row.metric_code, row.source_line_number) for row in self.expected]
        if len(keys) != len(set(keys)):
            raise ValueError("Reference metric/line pairs must be unique.")
        return self


class EvaluationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_name: str
    evaluation_type: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    report_json: dict[str, Any] | None = None


class EvaluationDocumentBasis(BaseModel):
    document_id: int
    title: str
    source_text_sha256: str
    source_content_hash: str
    line_count: int
    extractor_version: str
    is_mock: bool
