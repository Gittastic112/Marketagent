import { expect, test } from "@playwright/test";

import { backendData, createCompany, signIn } from "./helpers";


test("stored corpus search finds and filters owned research records", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const query = `conviction${unique}`;
  const company = await createCompany(page, {
    ticker: `Q${unique}`,
    local_symbol: `Q${unique}`,
    name: "Corpus Search E2E Fixture",
  });
  const thesis = await backendData<{ id: number }>(page, "/thesis-notes", {
    method: "POST",
    data: {
      company_id: company.id,
      title: `${query} thesis`,
      thesis_text: `Recurring revenue supports ${query}.`,
    },
  });
  const alert = await backendData<{ id: number }>(page, "/alerts", {
    method: "POST",
    data: {
      company_id: company.id,
      alert_type: "manual",
      title: `${query} alert`,
      summary: `New evidence changed ${query}.`,
    },
  });
  await backendData(page, "/decisions", {
    method: "POST",
    data: {
      company_id: company.id,
      decision_type: "Hold",
      rationale: `Maintain ${query} pending source review.`,
    },
  });
  const valuation = await backendData<{ id: number }>(page, `/companies/${company.id}/valuation-models`, {
    method: "POST",
    data: {
      company_id: company.id,
      name: `${query} valuation`,
      description: `Base case for ${query}.`,
    },
  });

  const apiResults = await backendData<Array<{ result_type: string }>>(
    page,
    `/search/evidence?q=${query}`,
  );
  expect(new Set(apiResults.map((result) => result.result_type))).toEqual(
    new Set(["alert", "decision", "thesis", "valuation"]),
  );

  await page.goto(`/search?q=${query}`);
  const results = page.getByRole("region", { name: "Search results" });
  await expect(results.getByRole("link", { name: `${query} thesis` })).toHaveAttribute(
    "href",
    `/thesis-notes/${thesis.id}`,
  );
  await expect(results.getByRole("link", { name: `${query} alert` })).toHaveAttribute(
    "href",
    `/alerts/${alert.id}`,
  );
  await expect(results.getByRole("link", { name: "Hold decision" })).toBeVisible();
  await expect(results.getByRole("link", { name: `${query} valuation` })).toHaveAttribute(
    "href",
    `/companies/${company.id}/valuation/${valuation.id}`,
  );

  await page.getByRole("combobox", { name: "Record type" }).selectOption("thesis");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page).toHaveURL(new RegExp(`q=${query}.*type=thesis|type=thesis.*q=${query}`));
  await expect(results.getByRole("link", { name: `${query} thesis` })).toBeVisible();
  await expect(results.getByRole("link", { name: `${query} alert` })).toHaveCount(0);
});
