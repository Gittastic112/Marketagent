import { expect, test } from "@playwright/test";

import { backendData, createCompany, signIn } from "./helpers";


function isoDate(offsetDays = 0) {
  const value = new Date();
  value.setUTCDate(value.getUTCDate() + offsetDays);
  return value.toISOString().slice(0, 10);
}

test("daily brief links evidence and never infers a zero portfolio move", async ({ page }) => {
  await signIn(page);
  const company = await createCompany(page, {
    ticker: "BRIEF",
    local_symbol: "BRIEF",
    name: "Briefing Runtime Company",
  });
  const source = await backendData<{ id: number }>(page, "/sources", {
    method: "POST",
    data: {
      name: "Briefing Runtime Official Source",
      source_type: "filing",
      base_url: "https://example.invalid/briefing-runtime",
      reliability_score: 95,
      active: true,
    },
  });
  const document = await backendData<{ id: number }>(page, "/raw-documents", {
    method: "POST",
    data: {
      company_id: company.id,
      source_id: source.id,
      document_type: "filing",
      title: "BRIEF annual filing",
      url: "https://example.invalid/briefing-runtime/filing",
      published_at: `${isoDate()}T08:00:00Z`,
      raw_text: "Revenue growth slowed while margins remained stable.",
      content_hash: "briefing-runtime-source-v1",
    },
  });
  const event = await backendData<{ id: number }>(page, "/events", {
    method: "POST",
    data: {
      company_id: company.id,
      raw_document_id: document.id,
      event_type: "SEC Filing",
      information_speed: "slow",
      title: "BRIEF filing update",
      description: "Revenue growth slowed while margins remained stable.",
      event_time: `${isoDate()}T08:00:00Z`,
      credibility_score: 95,
      novelty_score: 90,
      impact_score: 85,
      priority_score: 90,
    },
  });
  const portfolio = await backendData<{ id: number }>(page, "/portfolios", {
    method: "POST",
    data: { name: "Briefing Runtime Portfolio", base_currency: "USD" },
  });
  await backendData(page, "/portfolio-holdings", {
    method: "POST",
    data: {
      portfolio_id: portfolio.id,
      company_id: company.id,
      ticker: company.ticker,
      quantity: 4,
      average_cost: 95,
      currency: "USD",
      as_of_date: isoDate(),
    },
  });
  const previousPrice = await backendData<{ id: number }>(page, "/market-prices", {
    method: "POST",
    data: {
      company_id: company.id,
      ticker: company.ticker,
      price: 100,
      currency: "USD",
      as_of_date: isoDate(-1),
    },
  });
  const latestPrice = await backendData<{ id: number }>(page, "/market-prices", {
    method: "POST",
    data: {
      company_id: company.id,
      ticker: company.ticker,
      price: 110,
      currency: "USD",
      as_of_date: isoDate(),
    },
  });

  const brief = await backendData<{
    id: number;
    payload_json: {
      high_materiality_events: Array<{ event_id: number; raw_document_id: number | null }>;
      new_since_last_review: {
        filings: Array<{ event_id: number; raw_document_id: number | null }>;
        portfolio_moves: Array<{
          event_id: number;
          move_percent: number | null;
          calculation_status: string;
          source_market_price_ids: number[];
          affected_portfolios: Array<{ portfolio_id: number; portfolio_name: string }>;
        }>;
      };
      source_event_ids: number[];
      source_raw_document_ids: number[];
      source_market_price_ids: number[];
    };
  }>(page, "/daily-brief", { method: "POST", data: {} });

  const move = brief.payload_json.new_since_last_review.portfolio_moves.find(
    (candidate) => candidate.event_id === event.id,
  );
  expect(move).toBeTruthy();
  expect(move?.move_percent).toBeCloseTo(10);
  expect(move?.calculation_status).toBe("complete");
  expect(move?.source_market_price_ids).toEqual([previousPrice.id, latestPrice.id]);
  expect(move?.affected_portfolios).toContainEqual({
    portfolio_id: portfolio.id,
    portfolio_name: "Briefing Runtime Portfolio",
  });
  expect(brief.payload_json.high_materiality_events).toContainEqual(
    expect.objectContaining({ event_id: event.id, raw_document_id: document.id }),
  );
  expect(brief.payload_json.new_since_last_review.filings).toContainEqual(
    expect.objectContaining({ event_id: event.id, raw_document_id: document.id }),
  );
  expect(brief.payload_json.source_event_ids).toContain(event.id);
  expect(brief.payload_json.source_raw_document_ids).toContain(document.id);
  expect(brief.payload_json.source_market_price_ids).toEqual(
    expect.arrayContaining([previousPrice.id, latestPrice.id]),
  );

  const schedule = await backendData<{
    enabled: boolean;
    next_run_at: string | null;
    generation_mode: string;
  }>(page, "/daily-brief-schedule", {
    method: "PUT",
    data: {
      enabled: true,
      timezone: "UTC",
      local_time: "23:59:00",
      days_of_week: [0, 1, 2, 3, 4, 5, 6],
    },
  });
  expect(schedule.enabled).toBe(true);
  expect(schedule.next_run_at).toBeTruthy();
  expect(schedule.generation_mode).toBe("deterministic_no_external_ai");

  await backendData(page, `/daily-brief/${brief.id}/review`, { method: "PATCH", data: {} });
  await page.goto("/daily-brief");
  await expect(page.getByRole("heading", { name: "Daily Intelligence Brief" })).toBeVisible();
  await expect(
    page.getByText(
      /Authentication error|authentication is not configured|local session is missing or expired/i,
    ),
  ).toHaveCount(0);

  const portfolioMoveCard = page.locator("article").filter({
    has: page.getByRole("heading", { name: "BRIEF filing update", exact: true }),
  });
  await expect(portfolioMoveCard).toBeVisible();
  await expect(portfolioMoveCard.getByText("+10.00%", { exact: true })).toBeVisible();
  await expect(portfolioMoveCard.getByRole("link", { name: "Review event evidence" })).toHaveAttribute(
    "href",
    `/events/${event.id}/evidence-resolution`,
  );
  await expect(page.getByRole("link", { name: "Open source document" }).first()).toHaveAttribute(
    "href",
    `/documents/${document.id}/sections`,
  );
  await expect(page.getByText("Reviewed", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Local Brief Schedule" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Private research as generated" })).toBeVisible();
  await expect(page.getByText(/^Saved as generated \d{4}-/)).toBeVisible();
  const scheduleStatus = page
    .getByRole("main")
    .getByRole("complementary", { name: "Daily Brief schedule status" });
  await expect(scheduleStatus).toBeVisible();
  await expect(scheduleStatus.getByText("Rule-based, no external AI", { exact: true })).toBeVisible();
  await expect(scheduleStatus.getByText("Enabled", { exact: true })).toBeVisible();
});
