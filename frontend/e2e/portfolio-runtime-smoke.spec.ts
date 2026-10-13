import { expect, test } from "@playwright/test";

import { backendData, signIn } from "./helpers";


const PORTFOLIO_NAME = "Mock Data Multi-Currency Portfolio";
const START_DATE = "2026-07-20";
const END_DATE = "2026-08-10";

test("multi-currency portfolio comparison reconciles risk, FX, benchmark, and DCF evidence", async ({ page }) => {
  await signIn(page);
  const portfolios = await backendData<Array<{ id: number; name: string; base_currency: string }>>(page, "/portfolios");
  const portfolio = portfolios.find((candidate) => candidate.name === PORTFOLIO_NAME);
  expect(portfolio, "The isolated E2E seed must create the portfolio runtime fixture").toBeTruthy();
  expect(portfolio?.base_currency).toBe("USD");
  const portfolioId = portfolio!.id;
  const snapshots = await backendData<Array<{ calculation_status: string; payload_json: { replay_basis: { method: string; status: string; source_transaction_ids: number[] } } }>>(page, `/portfolio-snapshots?portfolio_id=${portfolioId}`);
  expect(snapshots).toHaveLength(2);
  for (const snapshot of snapshots) {
    expect(snapshot.payload_json.replay_basis.method).toBe("recorded-portfolio-replay-v1");
    expect(snapshot.payload_json.replay_basis.status).toBe("complete");
    expect(snapshot.payload_json.replay_basis.source_transaction_ids).toHaveLength(4);
  }

  const comparison = await backendData<{
    calculation_status: string;
    risk_calculation_status: string;
    expected_return_calculation_status: string;
    risk_covered_weight_percent: number;
    expected_return_coverage_percent: number;
    risk_reconciliation_error: number | null;
    holdings: Array<{
      ticker: string;
      aligned_observation_count: number;
      expected_return_claim_type: string;
      source_market_price_ids: number[];
      source_fx_observation_ids: number[];
      source_dcf_output_id: number | null;
    }>;
    source_market_price_ids: number[];
    source_fx_observation_ids: number[];
    source_dcf_output_ids: number[];
    contains_mock_data: boolean;
  }>(
    page,
    `/portfolios/${portfolioId}/risk-return-comparison?as_of_date=${END_DATE}&lookback_days=30&min_observations=20`,
  );
  expect(comparison.calculation_status).toBe("complete");
  expect(comparison.risk_calculation_status).toBe("complete");
  expect(comparison.expected_return_calculation_status).toBe("complete");
  expect(comparison.risk_covered_weight_percent).toBeCloseTo(100);
  expect(comparison.expected_return_coverage_percent).toBeCloseTo(100);
  expect(comparison.risk_reconciliation_error || 0).toBeCloseTo(0, 10);
  expect(comparison.source_market_price_ids).toHaveLength(44);
  expect(comparison.source_fx_observation_ids).toHaveLength(22);
  expect(comparison.source_dcf_output_ids).toHaveLength(2);
  expect(comparison.contains_mock_data).toBe(true);
  expect(comparison.holdings.map((holding) => holding.ticker).sort()).toEqual(["E2EEUR", "E2EUSD"]);
  expect(comparison.holdings.every((holding) => holding.aligned_observation_count === 21)).toBeTruthy();
  expect(comparison.holdings.every((holding) => holding.expected_return_claim_type === "Estimate")).toBeTruthy();
  expect(comparison.holdings.every((holding) => holding.source_dcf_output_id !== null)).toBeTruthy();

  const performance = await backendData<{
    time_weighted_return: { calculation_status: string; return_decimal: number | null; start_date: string | null; end_date: string };
    money_weighted_return: { calculation_status: string; return_decimal: number | null; start_date: string | null; end_date: string };
  }>(page, `/portfolios/${portfolioId}/performance?start_date=${START_DATE}&end_date=${END_DATE}`);
  expect(performance.time_weighted_return.calculation_status).toBe("complete");
  expect(performance.time_weighted_return.return_decimal).not.toBeNull();
  expect(performance.money_weighted_return.calculation_status).toBe("complete");
  expect(performance.money_weighted_return.return_decimal).not.toBeNull();

  const attribution = await backendData<{
    calculation_status: string;
    fx_impact: number | null;
    unexplained_change: number | null;
    blockers: string[];
    source_snapshot_ids: number[];
  }>(page, `/portfolios/${portfolioId}/period-attribution?start_date=${START_DATE}&end_date=${END_DATE}`);
  expect(attribution.calculation_status).toBe("complete");
  expect(attribution.fx_impact).not.toBeNull();
  expect(attribution.fx_impact).toBeGreaterThan(0);
  expect(attribution.unexplained_change || 0).toBeCloseTo(0, 8);
  expect(attribution.blockers).toEqual([]);
  expect(attribution.source_snapshot_ids).toHaveLength(2);

  const opportunity = await backendData<{
    calculation_status: string;
    benchmark_ticker: string | null;
    opportunity_cost: number | null;
    source_snapshot_ids: number[];
    source_market_price_ids: number[];
  }>(page, `/portfolios/${portfolioId}/opportunity-cost?start_date=${START_DATE}&end_date=${END_DATE}`);
  expect(opportunity.calculation_status).toBe("complete");
  expect(opportunity.benchmark_ticker).toBe("E2EBMK");
  expect(opportunity.opportunity_cost).not.toBeNull();
  expect(opportunity.source_snapshot_ids).toHaveLength(2);
  expect(opportunity.source_market_price_ids).toHaveLength(2);

  await page.goto(`/portfolio/${portfolioId}?start_date=${START_DATE}&end_date=${END_DATE}`);
  await expect(page.getByRole("heading", { name: PORTFOLIO_NAME })).toBeVisible();
  const performancePanel = page.getByRole("heading", {name: "Period Performance & Attribution"}).locator("xpath=../..");
  const twrCard = performancePanel.getByText("TWR: selected period (complete)", {exact: true}).locator("..");
  const mwrCard = performancePanel.getByText("MWR: annualized (complete)", {exact: true}).locator("..");
  const twrDates = `Period: ${performance.time_weighted_return.start_date} to ${performance.time_weighted_return.end_date}. Not annualized.`;
  const mwrDates = `Since first cash flow: ${performance.money_weighted_return.start_date} to ${performance.money_weighted_return.end_date}.`;
  expect(performance.time_weighted_return.start_date).toBe(START_DATE);
  expect(performance.money_weighted_return.start_date).not.toBeNull();
  await expect(twrCard.getByText(twrDates, {exact: true})).toBeVisible();
  await expect(mwrCard.getByText(mwrDates, {exact: true})).toBeVisible();
  const comparisonPanel = page.getByRole("heading", { name: "Marginal Risk & DCF Valuation Gap" }).locator("xpath=../..");
  await expect(comparisonPanel.getByText("Mock Data", { exact: true })).toBeVisible();
  await expect(comparisonPanel.getByText("E2EUSD")).toBeVisible();
  await expect(comparisonPanel.getByText("E2EEUR")).toBeVisible();
  await expect(comparisonPanel.getByText("100.0% covered")).toHaveCount(2);
  await expect(comparisonPanel.getByText("Estimate", { exact: true })).toHaveCount(2);
  await expect(comparisonPanel.getByText(/not an annualized forecast/i)).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("performance-risk-desktop.png"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(twrCard.getByText(twrDates, {exact: true})).toBeVisible();
  await expect(mwrCard.getByText(mwrDates, {exact: true})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
  await page.screenshot({ path: test.info().outputPath("performance-risk-mobile.png"), fullPage: true });
  await page.goto(`/portfolio/${portfolioId}?tab=setup`);
  await expect(page.getByText("Recorded activity reconciled", { exact: true })).toHaveCount(2);
  await page.screenshot({ path: test.info().outputPath("replayed-history-mobile.png"), fullPage: true });
});
