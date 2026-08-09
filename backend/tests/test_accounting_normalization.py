import pytest
from app.services.accounting_normalization import RDCapitalizationService, GoodwillDiagnosticsService

def test_rd_capitalization():
    current_rd = 100.0
    # 1Y, 2Y, 3Y, 4Y, 5Y
    historical_rd = [80.0, 70.0, 60.0, 50.0, 40.0]

    result = RDCapitalizationService.calculate_capitalized_rd(current_rd, historical_rd)

    # R&D Asset = 100 + (0.8*80) + (0.6*70) + (0.4*60) + (0.2*50)
    # 100 + 64 + 42 + 24 + 10 = 240
    assert result["rd_asset"] == 240.0

    # Amortization = (80 + 70 + 60 + 50 + 40) / 5
    # 300 / 5 = 60
    assert result["rd_amortization"] == 60.0

def test_rd_capitalization_missing_history():
    current_rd = 100.0
    # only 2 years of history
    historical_rd = [80.0, 70.0]

    result = RDCapitalizationService.calculate_capitalized_rd(current_rd, historical_rd)

    # R&D Asset = 100 + (0.8*80) + (0.6*70) + 0 + 0
    # 100 + 64 + 42 = 206
    assert result["rd_asset"] == 206.0

    # Amortization = (80 + 70 + 0 + 0 + 0) / 5
    # 150 / 5 = 30
    assert result["rd_amortization"] == 30.0

def test_adjusted_metrics():
    reported_ebit = 500.0
    reported_ic = 1000.0

    # Using the first test's results
    current_rd = 100.0
    rd_asset = 240.0
    rd_amortization = 60.0

    metrics = RDCapitalizationService.calculate_adjusted_metrics(reported_ebit, reported_ic, current_rd, rd_asset, rd_amortization)

    # Adjusted EBIT = 500 + 100 - 60 = 540
    assert metrics["adjusted_ebit"] == 540.0
    # Adjusted IC = 1000 + 240 = 1240
    assert metrics["adjusted_invested_capital"] == 1240.0
    # Adjusted ROC = 540 / 1240 = 0.43548
    assert round(metrics["adjusted_roc"], 5) == 0.43548

def test_goodwill_diagnostics():
    result1 = GoodwillDiagnosticsService.diagnose(goodwill=300.0, total_assets=1000.0, impairment_expense=0.0)
    assert result1["acquisition_heavy"] is True
    assert len(result1["warnings"]) == 1

    result2 = GoodwillDiagnosticsService.diagnose(goodwill=100.0, total_assets=1000.0, impairment_expense=50.0)
    assert result2["acquisition_heavy"] is False
    assert len(result2["warnings"]) == 1
    assert "Recent Impairment" in result2["warnings"][0]
