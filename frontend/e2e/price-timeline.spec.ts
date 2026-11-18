import { expect, test } from "@playwright/test";
import { backendData, signIn } from "./helpers";

test("inspect a marked close, pin to a private thesis and reopen its chart", async ({ page }) => {
  await signIn(page);
  const companies = await backendData<{ id: number; ticker: string }[]>(page, "/companies");
  const company = companies.find(c => c.ticker === "E2ECHART")!;
  const note = await backendData<{ id: number; title: string }>(page, "/thesis-notes", {
    method: "POST", data: { company_id: company.id, title: "Mock Data chart thesis", thesis_text: "Browser fixture" },
  });
  try {
    await page.goto(`/companies/${company.id}#price-history`);
    const chart = page.getByRole("region", { name: "Stock price history" });
    await expect(chart.getByText(/Mock Data · E2e/)).toBeVisible();
    await expect(chart.locator(".recharts-line-curve")).toBeVisible();
    await chart.getByRole("combobox", { name: /^Inspect date/ }).selectOption("2026-01-07");
    await chart.getByRole("button", { name: "Open point details" }).click();
    await expect(page.getByRole("region", { name: "Preceding close coverage" }).getByRole("link", { name: "Mock Data earnings filing" })).toBeVisible();
    await page.keyboard.press("Escape");
    await chart.getByLabel("Key moments").selectOption("2026-01-06");
    const details = page.getByRole("dialog");
    await expect(details.getByText(/-10% from the stored close/)).toBeVisible();
    await expect(details.getByRole("link", { name: "Mock Data earnings filing" })).toBeVisible();
    await details.getByLabel("Attach to thesis").selectOption(String(note.id));
    await details.getByLabel("Note on this close").fill("Mock Data check the next disclosure");
    await details.getByRole("button", { name: "Pin to thesis" }).click();
    await expect(details.getByRole("status")).toHaveText("Saved to your thesis.");
    await details.getByRole("link", { name: note.title }).click();
    await expect(page.locator("#price-pins")).toContainText("Mock Data check the next disclosure");
    await page.locator("#price-pins a").first().click();
    await chart.getByRole("button", { name: "Open point details" }).click();
    await expect(details.getByText("Mock Data check the next disclosure")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(details).not.toBeVisible();
  } finally {
    await backendData(page, `/thesis-notes/${note.id}`, { method: "DELETE" });
  }
});
