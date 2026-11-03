from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class DamodaranMarginBenchmark(Base):
    __tablename__ = "damodaran_industry_margin_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    number_of_firms = Column(Integer, nullable=True)

    gross_margin = Column(Float, nullable=True)
    ebitda_margin = Column(Float, nullable=True)
    ebit_margin = Column(Float, nullable=True)
    net_margin = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DamodaranCapexBenchmark(Base):
    __tablename__ = "damodaran_industry_capex_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)

    capex_to_sales = Column(Float, nullable=True)
    net_capex_to_sales = Column(Float, nullable=True)
    sales_to_capital = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class DamodaranWcBenchmark(Base):
    __tablename__ = "damodaran_industry_working_capital_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    number_of_firms = Column(Integer, nullable=True)

    wc_to_sales = Column(Float, nullable=True)
    non_cash_wc_to_sales = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DamodaranRoeBenchmark(Base):
    __tablename__ = "damodaran_industry_roe_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    number_of_firms = Column(Integer, nullable=True)

    roe = Column(Float, nullable=True)
    rd_adjusted_roe = Column(Float, nullable=True)
    roc = Column(Float, nullable=True)
    roic = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DamodaranGrowthBenchmark(Base):
    __tablename__ = "damodaran_industry_fundamental_growth"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)

    expected_revenue_growth = Column(Float, nullable=True)
    expected_revenue_growth_2y = Column(Float, nullable=True)
    expected_revenue_growth_5y = Column(Float, nullable=True)
    expected_ebit_growth = Column(Float, nullable=True)
    expected_eps_growth = Column(Float, nullable=True)
    historical_net_income_growth = Column(Float, nullable=True)
    historical_revenue_growth = Column(Float, nullable=True)
    historical_ebit_growth = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DamodaranFinancingFlowsBenchmark(Base):
    __tablename__ = "damodaran_industry_financing_flows"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)

    debt_to_equity = Column(Float, nullable=True)
    debt_to_capital = Column(Float, nullable=True)
    effective_tax_rate = Column(Float, nullable=True)

    number_of_firms = Column(Integer, nullable=True)
    dividends_usd_millions = Column(Float, nullable=True)
    buybacks_usd_millions = Column(Float, nullable=True)
    equity_issuance_usd_millions = Column(Float, nullable=True)
    net_equity_change_usd_millions = Column(Float, nullable=True)
    net_equity_change_to_book_equity = Column(Float, nullable=True)
    debt_repaid_usd_millions = Column(Float, nullable=True)
    debt_raised_usd_millions = Column(Float, nullable=True)
    net_debt_change_usd_millions = Column(Float, nullable=True)
    net_debt_change_to_total_debt = Column(Float, nullable=True)
    lease_debt_change_usd_millions = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RegressionModelCoefficient(Base):
    __tablename__ = "regression_model_coefficients"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    variable_name = Column(String(100), nullable=False)
    coefficient_value = Column(Float, nullable=False)
    region = Column(String(100), nullable=True)
    version_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DamodaranPricingBenchmark(Base):
    __tablename__ = "damodaran_industry_pricing_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    number_of_firms = Column(Integer, nullable=True)

    # peIndia.xls
    pe_current = Column(Float, nullable=True)
    pe_trailing = Column(Float, nullable=True)
    pe_forward = Column(Float, nullable=True)
    peg_ratio = Column(Float, nullable=True)
    percent_money_losing = Column(Float, nullable=True)
    pe_aggregate_all_firms = Column(Float, nullable=True)
    pe_aggregate_money_making = Column(Float, nullable=True)
    expected_growth_next_five_years = Column(Float, nullable=True)

    # pbvIndia.xls
    pbv_ratio = Column(Float, nullable=True)
    ev_to_invested_capital = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    roic = Column(Float, nullable=True)

    # psIndia.xls
    ps_ratio = Column(Float, nullable=True)
    ev_to_sales = Column(Float, nullable=True)
    net_margin = Column(Float, nullable=True)
    pretax_operating_margin = Column(Float, nullable=True)

    # vebitdaIndia.xls
    ev_to_ebitda_positive_ebitda = Column(Float, nullable=True)
    ev_to_ebitda_all = Column(Float, nullable=True)
    ev_to_ebit_positive_ebitda = Column(Float, nullable=True)
    ev_to_ebit_all = Column(Float, nullable=True)
    ev_to_ebitda_rd_positive_ebitda = Column(Float, nullable=True)
    ev_to_ebitda_rd_all = Column(Float, nullable=True)
    ev_to_after_tax_ebit_positive_ebitda = Column(Float, nullable=True)
    ev_to_after_tax_ebit_all = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DamodaranDividendBenchmark(Base):
    __tablename__ = "damodaran_industry_dividend_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    number_of_firms = Column(Integer, nullable=True)

    dividend_yield = Column(Float, nullable=True)
    payout_ratio = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DamodaranFCFEBenchmark(Base):
    __tablename__ = "damodaran_industry_fcfe_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    number_of_firms = Column(Integer, nullable=True)

    net_income = Column(Float, nullable=True)
    capex_minus_depreciation = Column(Float, nullable=True)
    change_in_wc = Column(Float, nullable=True)
    net_debt_issued = Column(Float, nullable=True)
    fcfe = Column(Float, nullable=True)
    fcfe_before_debt = Column(Float, nullable=True)
    fcfe_after_debt = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CountryMarketStats(Base):
    __tablename__ = "country_market_stats"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=True)
    country = Column(String(100), nullable=False, index=True)

    firm_count = Column(Integer, nullable=True)
    market_cap_usd_millions = Column(Float, nullable=True)
    total_debt_usd_millions = Column(Float, nullable=True)
    firm_value_usd_millions = Column(Float, nullable=True)
    cash_usd_millions = Column(Float, nullable=True)
    enterprise_value_usd_millions = Column(Float, nullable=True)

    median_current_pe = Column(Float, nullable=True)
    median_trailing_pe = Column(Float, nullable=True)
    median_forward_pe = Column(Float, nullable=True)
    median_peg = Column(Float, nullable=True)
    median_pbv = Column(Float, nullable=True)
    median_ps = Column(Float, nullable=True)
    median_ev_ebit = Column(Float, nullable=True)
    median_ev_ebitda = Column(Float, nullable=True)
    median_ev_invested_capital = Column(Float, nullable=True)
    median_ev_sales = Column(Float, nullable=True)
    median_cash_to_firm_value = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    total_dividends_usd_millions = Column(Float, nullable=True)

    date_updated = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
