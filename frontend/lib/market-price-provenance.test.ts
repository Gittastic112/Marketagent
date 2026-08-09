import assert from "node:assert/strict";
import { test } from "node:test";

import type { MarketPrice } from "./api.ts";
import { marketPriceSource, marketPriceTiming } from "./market-price-provenance.ts";

function price(overrides: Partial<MarketPrice> = {}): MarketPrice {
  return {
    id: 1,
    company_id: 1,
    ticker: "AAPL",
    price: 200,
    currency: "USD",
    as_of_date: "2026-08-01",
    created_at: "2026-08-01T10:00:00Z",
    updated_at: "2026-08-01T10:00:00Z",
    ...overrides
  };
}

test("marketPriceSource labels manual and unofficial data distinctly", () => {
  assert.deepEqual(marketPriceSource(price({ provider_name: "manual" })), {
    label: "Manual entry",
    tone: "default"
  });
  assert.deepEqual(marketPriceSource(price({ provider_name: "yfinance_personal" })), {
    label: "yfinance (unofficial)",
    tone: "warning"
  });
});

test("marketPriceSource keeps unknown legacy provenance visible", () => {
  assert.deepEqual(marketPriceSource(price({ provider_name: "legacy_unknown" })), {
    label: "Legacy source",
    tone: "warning"
  });
});

test("marketPriceTiming exposes timing, delay, and adjustment state", () => {
  assert.equal(
    marketPriceTiming(
      price({ price_type: "end_of_day", delay_minutes: 15, adjustment_state: "unadjusted" })
    ),
    "end of day / 15 min delay / unadjusted"
  );
});
