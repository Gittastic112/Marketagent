from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, func, JSON
from app.db.base import Base

class IndustryVolatilityBenchmark(Base):
    __tablename__ = "industry_volatility_benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_file_id = Column(
        Integer,
        ForeignKey("damodaran_dataset_files.id"),
        nullable=True,
        index=True,
    )
    country = Column(String, nullable=False)
    region = Column(String, nullable=True)
    data_date = Column(Date, nullable=True)
    industry_name = Column(String, nullable=False)

    number_of_firms = Column(Integer, nullable=True)
    equity_standard_deviation = Column(Float, nullable=True)
    firm_value_standard_deviation = Column(Float, nullable=True)
    equity_value_weight = Column(Float, nullable=True)
    debt_value_weight = Column(Float, nullable=True)

    assumed_debt_to_equity_vol_ratio = Column(Float, default=0.40)
    assumed_debt_equity_correlation = Column(Float, default=0.50)

    source_file = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

class RealOptionAssumption(Base):
    __tablename__ = "real_option_assumptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    valuation_id = Column(Integer, ForeignKey("dcf_assumption_sets.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)

    option_type = Column(String, nullable=False)
    option_name = Column(String, nullable=True)

    underlying_asset_value = Column(Float, nullable=False)
    exercise_price = Column(Float, nullable=False)
    option_life_years = Column(Float, nullable=False)
    risk_free_rate = Column(Float, nullable=False)
    volatility = Column(Float, nullable=False)
    dividend_yield_or_cost_of_delay = Column(Float, default=0)

    exclusivity_score = Column(Float, default=1)
    development_lag_years = Column(Float, nullable=True)
    source_of_volatility = Column(String, nullable=True)
    source_of_underlying_value = Column(String, nullable=True)

    created_at = Column(DateTime, default=func.now())

class RealOptionResult(Base):
    __tablename__ = "real_option_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    real_option_assumption_id = Column(Integer, ForeignKey("real_option_assumptions.id"), nullable=False)
    valuation_id = Column(Integer, ForeignKey("dcf_assumption_sets.id"), nullable=False)

    d1 = Column(Float, nullable=True)
    d2 = Column(Float, nullable=True)
    nd1 = Column(Float, nullable=True)
    nd2 = Column(Float, nullable=True)

    raw_option_value = Column(Float, nullable=True)
    adjusted_option_value = Column(Float, nullable=True)
    option_delta = Column(Float, nullable=True)
    option_value_pct_base_dcf = Column(Float, nullable=True)

    eligibility_passed = Column(Boolean, nullable=True)
    eligibility_warnings = Column(JSON, nullable=True)
    double_counting_warnings = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=func.now())

class OptionEligibilityTest(Base):
    __tablename__ = "option_eligibility_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    valuation_id = Column(Integer, ForeignKey("dcf_assumption_sets.id"), nullable=False)
    option_type = Column(String, nullable=False)

    has_underlying_asset = Column(Boolean, nullable=True)
    has_finite_life = Column(Boolean, nullable=True)
    has_clear_exercise_price = Column(Boolean, nullable=True)
    has_asymmetric_payoff = Column(Boolean, nullable=True)
    has_exclusivity = Column(Boolean, nullable=True)
    can_estimate_volatility = Column(Boolean, nullable=True)
    can_estimate_underlying_value = Column(Boolean, nullable=True)

    eligibility_score = Column(Float, nullable=True)
    recommendation = Column(String, nullable=True)

    created_at = Column(DateTime, default=func.now())
