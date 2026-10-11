import assert from "node:assert/strict";
import test from "node:test";
import { portfolioDate } from "./portfolio-period.ts";

test("portfolio dates reject invalid dates, duplicate query values and query injection", () => {
  for (const value of [undefined, ["2024-01-02"], "2024-02-30", "2024-13-01", "x", "2024-01-02&as_of_date=2025-01-01"]) {
    assert.equal(portfolioDate(value), null);
  }
  assert.equal(portfolioDate("2024-01-02"), "2024-01-02");
  assert.equal(portfolioDate("2024-02-29"), "2024-02-29");
});
