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
    const pinLink = page.locator("#price-pins a").first();
    await expect(pinLink).toHaveAttribute("href", /thesis=\d+&pin=\d+/);
    await pinLink.click();
    await chart.getByRole("button", { name: "Open point details" }).click();
    await expect(details.getByText("Mock Data check the next disclosure")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(details).not.toBeVisible();
    const pin = (await backendData<{ id: number; anchor: { price_id: number; price: string; currency: string } }[]>(page, `/thesis-notes/${note.id}/price-pins`))[0];
    const original = Number(pin.anchor.price);
    try {
      await backendData(page, `/market-prices/${pin.anchor.price_id}`, {method: "PATCH", data: {price: original + 3}});
      await page.reload();
      await expect(chart.getByText(`Current stored close for that date · ${pin.anchor.currency} ${original + 3}`)).toBeVisible();
      await expect(chart.getByText(/Close when pinned/)).toContainText(pin.anchor.price);
      await chart.getByRole("button", { name: "Open point details" }).click();
      await expect(details.getByText("Mock Data check the next disclosure")).toHaveCount(0);
    } finally {
      await backendData(page, `/market-prices/${pin.anchor.price_id}`, {method: "PATCH", data: {price: original}});
    }
  } finally {
    await backendData(page, `/thesis-notes/${note.id}`, { method: "DELETE" });
  }
});

for (const width of [1440, 390]) {
  test(`fractional thesis drift persists once at width ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 900 });
    await signIn(page);
    const companies = await backendData<{ id: number; ticker: string }[]>(page, "/companies");
    const company = companies.find(c => c.ticker === "E2ECHART")!;
    const note = await backendData<{ id: number }>(page, "/thesis-notes", { method: "POST", data: {
      company_id: company.id, title: "Mock Data drift review", thesis_text: "Synthetic review fixture" } });
    try {
      await page.goto(`/thesis-notes/${note.id}`);
      const form = page.getByRole("form", { name: "Create change" });
      await form.getByLabel("Change Summary").fill("Mock Data updated a thesis assumption");
      const score = form.getByLabel("Drift Score");
      await score.fill("0.25");
      expect(await score.evaluate(el => (el as HTMLInputElement).checkValidity())).toBe(true);
      await score.press("Enter");
      await expect(page.getByText(/Status:.*Drift: 0.25/)).toBeVisible();
      const saved = await backendData<{thesis_drift_score: number; changes: {drift_score: number}[]}>(page, `/thesis-notes/${note.id}`);
      expect(saved.thesis_drift_score).toBe(0.25);
      expect(saved.changes.map(c => c.drift_score)).toEqual([0.25]);
    } finally {
      await backendData(page, `/thesis-notes/${note.id}`, { method: "DELETE" });
    }
  });
}
