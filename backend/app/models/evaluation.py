from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Historical runs have no provable owner and remain inaccessible to user lists.
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    report_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    run_name: Mapped[str] = mapped_column(String(200))
    evaluation_type: Mapped[str] = mapped_column(String(50))  # e.g., 'financial', 'event', 'alert', 'ai', 'valuation'
    status: Mapped[str] = mapped_column(String(50), default="running")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FinancialExtractionEval(Base):
    __tablename__ = "financial_extraction_evals"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("raw_documents.id"), index=True)

    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    period_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_locator_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    manual_intervention_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventExtractionEval(Base):
    __tablename__ = "event_extraction_evals"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("raw_documents.id"), index=True)

    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    duplicate_suppression_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    false_positive_count: Mapped[int] = mapped_column(Integer, default=0)
    missed_material_events_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertEval(Base):
    __tablename__ = "alert_evals"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True)

    user_classification: Mapped[str] = mapped_column(String(50)) # 'useful', 'not useful', 'false positive', 'already known', 'needs follow-up'

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ValuationEval(Base):
    __tablename__ = "valuation_evals"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True)
    valuation_model_id: Mapped[int] = mapped_column(ForeignKey("valuation_models.id"), index=True)

    reproducibility_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    guardrail_behavior_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    accounting_bridge_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    scenario_behavior_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    reverse_dcf_passed: Mapped[bool] = mapped_column(Boolean, default=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
