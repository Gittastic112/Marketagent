import assert from "node:assert/strict";
import test from "node:test";
import type { Company } from "./api/companies.ts";
import { matchingResearchCompanies, researchResultHref } from "./research-search.ts";

test("search destinations reject arbitrary external, executable and non-research routes", () => {
  assert.equal(researchResultHref("/companies/7/valuation/9?version=11#source"), "/companies/7/valuation/9?version=11#source");
  assert.equal(researchResultHref("/documents/12?page=3"), "/documents/12?page=3");
  for (const href of ["https://evil.test", "//evil.test", "javascript:alert(1)", "/\\evil.test", "/api/backend/delete", "/auth/signout", "/companies/../../auth/signout"]) {
    assert.equal(researchResultHref(href), null, href);
  }
});

test("company matching preserves exchange identity and ranks exact tickers without altering source data", () => {
  const companies = [
    { id: 2, ticker: "ABC", name: "India Example", market: "IN", primary_exchange: "NSE", aliases_json: [] },
    { id: 1, ticker: "ABC", name: "US Example", market: "US", primary_exchange: "NYSE", aliases_json: [] },
    { id: 3, ticker: "ZZZ", name: "ABC supplier", market: "US", primary_exchange: "NASDAQ", aliases_json: ["Old Name"] },
  ] as unknown as Company[];
  assert.deepEqual(matchingResearchCompanies(companies, "ABC", "").map(company => company.id), [1, 2, 3]);
  assert.deepEqual(matchingResearchCompanies(companies, "ABC", "IN").map(company => company.id), [2]);
  assert.deepEqual(matchingResearchCompanies(companies, "old name", "").map(company => company.id), [3]);
  assert.deepEqual(companies.map(company => company.id), [2, 1, 3]);
});
