from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import ForeignKey, String, Float, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class ValuationModel(Base):
    __tablename__ = "valuation_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    model_type: Mapped[str] = mapped_column(String, default="fcff_dcf") # fcff_dcf, reverse_dcf, etc.

    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    company = relationship("Company")
    assumption_sets = relationship("DcfAssumptionSet", back_populates="valuation_model", cascade="all, delete-orphan")
    decision_logs = relationship("DcfDecisionLog", back_populates="valuation_model", cascade="all, delete-orphan")
    assumption_provenances = relationship("ValuationAssumptionProvenance", back_populates="valuation", cascade="all, delete-orphan")


class ValuationSetupDraft(Base):
    __tablename__ = "valuation_setup_drafts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    promoted_model_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("valuation_models.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    industry_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    assumptions_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    warnings_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    reviewed_fields_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    edited_fields_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    company = relationship("Company")
    promoted_model = relationship("ValuationModel")


class DcfAssumptionSet(Base):
    __tablename__ = "dcf_assumption_sets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    valuation_model_id: Mapped[int] = mapped_column(ForeignKey("valuation_models.id", ondelete="CASCADE"), index=True)
    scenario: Mapped[str] = mapped_column(String, default="Base") # Base, Bull, Bear

    # Story-based Valuation
    story_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    growth_story: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    margin_story: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reinvestment_story: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    risk_story: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Core Assumptions
    projection_years_count: Mapped[int] = mapped_column(Integer, default=10)
    starting_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_growth_years_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    target_operating_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_operating_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tax_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sales_to_capital_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reinvestment_method: Mapped[str] = mapped_column(String, default="sales_to_capital")
    starting_invested_capital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Cost of Capital
    risk_free_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity_risk_premium: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    beta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_of_equity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pre_tax_cost_of_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    debt_to_capital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity_to_capital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wacc_start: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wacc_terminal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Terminal Value
    terminal_growth_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    terminal_roic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Bridge to Equity
    cash: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cross_holdings: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    minority_interests: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    preferred_stock: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    operating_leases: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    employee_options_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    diluted_shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    basic_shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_market_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cash_flow_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    discount_rate_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    currency_override_note: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    valuation_model = relationship("ValuationModel", back_populates="assumption_sets")
    # Phase 11 additions: FCFE, Dividends, Buybacks
    net_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    capex: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depreciation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    change_in_nwc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_debt_issued: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    debt_repaid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dividends: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    buybacks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stock_issuances: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    company_age: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Phase 18: Market Intelligence Integration
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    stale_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    stale_event_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("events.id"), nullable=True)

    # Phase 16: Lifecycle and Special Cases
    probability_of_failure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    distress_sale_proceeds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    book_value_of_equity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    outputs = relationship("DcfOutput", back_populates="assumption_set", cascade="all, delete-orphan", uselist=False)
    projection_years = relationship("DcfProjectionYear", back_populates="assumption_set", cascade="all, delete-orphan")
    sensitivity_tables = relationship("DcfSensitivityTable", back_populates="assumption_set", cascade="all, delete-orphan")
    decision_logs = relationship("DcfDecisionLog", back_populates="assumption_set", cascade="all, delete-orphan")
    change_logs = relationship("ValuationAssumptionChangeLog", back_populates="assumption_set", cascade="all, delete-orphan")


class DcfProjectionYear(Base):
    __tablename__ = "dcf_projection_years"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assumption_set_id: Mapped[int] = mapped_column(ForeignKey("dcf_assumption_sets.id", ondelete="CASCADE"), index=True)
    year_index: Mapped[int] = mapped_column(index=True)
    calendar_year: Mapped[int] = mapped_column(index=True)

    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_growth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tax_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nopat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reinvestment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fcff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    invested_capital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wacc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discount_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pv_fcff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    assumption_set = relationship("DcfAssumptionSet", back_populates="projection_years")


class DcfOutput(Base):
    __tablename__ = "dcf_outputs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assumption_set_id: Mapped[int] = mapped_column(ForeignKey("dcf_assumption_sets.id", ondelete="CASCADE"), index=True)

    sum_pv_fcff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    terminal_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pv_terminal_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    enterprise_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    cash: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cross_holdings: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    non_operating_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    operating_leases: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    minority_interests: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    preferred_stock: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    employee_options_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    equity_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    diluted_shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intrinsic_value_per_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_market_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    upside_downside_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    terminal_value_pct_of_ev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    implied_exit_multiple: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    implied_terminal_roic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Phase 16 outputs
    base_dcf_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pv_of_excess_returns: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    implied_pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    implied_ev_ebitda: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    implied_ev_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    implied_ev_ebit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    implied_pbv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    warnings_json: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)

    # Phase 11 additions
    fcfe_intrinsic_value_per_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ddm_intrinsic_value_per_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    assumption_set = relationship("DcfAssumptionSet", back_populates="outputs")


class DcfSensitivityTable(Base):
    __tablename__ = "dcf_sensitivity_tables"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assumption_set_id: Mapped[int] = mapped_column(ForeignKey("dcf_assumption_sets.id", ondelete="CASCADE"), index=True)
    table_type: Mapped[str] = mapped_column(String) # e.g. wacc_vs_terminal_growth

    x_axis_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    y_axis_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    values_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    assumption_set = relationship("DcfAssumptionSet", back_populates="sensitivity_tables")


class DcfDecisionLog(Base):
    __tablename__ = "dcf_decision_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    valuation_model_id: Mapped[int] = mapped_column(ForeignKey("valuation_models.id", ondelete="CASCADE"), index=True)
    assumption_set_id: Mapped[int] = mapped_column(ForeignKey("dcf_assumption_sets.id", ondelete="CASCADE"), index=True)

    decision_type: Mapped[str] = mapped_column(String) # watch, research_more, etc.
    user_note: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    price_at_decision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intrinsic_value_at_decision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    upside_downside_at_decision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_label: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    valuation_model = relationship("ValuationModel", back_populates="decision_logs")
    assumption_set = relationship("DcfAssumptionSet", back_populates="decision_logs")


class ValuationAssumptionChangeLog(Base):
    __tablename__ = "valuation_assumption_change_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    valuation_model_id: Mapped[int] = mapped_column(ForeignKey("valuation_models.id", ondelete="CASCADE"), index=True)
    assumption_set_id: Mapped[int] = mapped_column(ForeignKey("dcf_assumption_sets.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), index=True, nullable=True)

    parameter_name: Mapped[str] = mapped_column(String) # e.g. "terminal_growth_rate", "target_operating_margin"
    old_value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    is_applied: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    valuation_model = relationship("ValuationModel")
    assumption_set = relationship("DcfAssumptionSet", back_populates="change_logs")
    event = relationship("Event")
