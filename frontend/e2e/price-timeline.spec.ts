import { expect, test } from "@playwright/test";
import { backendData, signIn } from "./helpers";

test("inspect a marked close, pin to a private thesis and reopen its chart", async ({ page }) => {
  await signIn(page);
  const companies = await backendData<{ id: number; ticker: string }[]>(page, "/companies");
  const company = companies.find(c => c.ticker === "E2ECHART")!;
  const note = await backendData<{ id: number; title: string }>(page, "/thesis-notes", {
    method: "POST", data: { company_id: company.id, title: "Mock Data chart thesis", thesis_text: "Browser fixture" },
  });
  const pinText = `Mock Data check the next disclosure for thesis ${note.id}`;
  try {
    const assumption = await backendData<{ id: number }>(page, `/thesis-notes/${note.id}/assumptions`, {
      method: "POST", data: { thesis_note_id: note.id, description: "Mock Data margins recover after the filing" },
    });
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
    await details.getByRole("link", { name: "Mock Data earnings filing" }).click();
    await expect(page.getByRole("heading", { name: "Mock Data earnings filing" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Open original source" })).toHaveAttribute("href", "https://example.invalid/mock-data/chart-filing");
    await page.getByRole("link", { name: "Return to selected close" }).click();
    await expect(chart.getByRole("combobox", { name: /^Inspect date/ })).toHaveValue("2026-01-06");
    await chart.getByRole("button", { name: "Open point details" }).click();
    await details.getByLabel("Attach to thesis").selectOption(String(note.id));
    await details.getByLabel("Note on this close").fill(pinText);
    await details.getByRole("button", { name: "Pin to thesis" }).click();
    await expect(details.getByRole("status")).toHaveText("Saved to your thesis.");
    await details.getByRole("listitem").filter({ hasText: pinText }).getByRole("link", { name: note.title, exact: true }).click();
    await expect(page.locator("#price-pins")).toContainText(pinText);
    const pinLink = page.locator("#price-pins a").first();
    await expect(pinLink).toHaveAttribute("href", /thesis=\d+&pin=\d+/);
    await pinLink.click();
    await chart.getByRole("button", { name: "Open point details" }).click();
    await expect(details.getByText(pinText)).toBeVisible();
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
      await expect(details.getByText(pinText)).toHaveCount(0);
      await page.goto(`/thesis-notes/${note.id}#price-pins`);
      await page.getByRole("button", {name: "Review this observation"}).click();
      await page.getByLabel("Thesis assumption").selectOption(String(assumption.id));
      await page.getByLabel("Original evidence").selectOption("0");
      await page.getByRole("combobox", {name: "Decision", exact: true}).selectOption("propose_change");
      const reason = "Compare the recorded margin assumption with the next original filing";
      await page.getByLabel("Reason for the decision").fill(reason);
      await page.getByRole("button", {name: "Preview thesis decision"}).click();
      await expect(page.getByRole("group", {name: "Decision about the thesis"})).toContainText(pin.anchor.price);
      await page.getByRole("button", {name: "Save to thesis history"}).click();
      await expect(page.getByRole("row").filter({hasText: reason})).toContainText("Mock Data earnings filing");
      await page.reload();
      const history = await backendData<{changes: {price_review: {decision: string; anchor: {price: string}; assumption: {id: number}}}[]}>(page, `/thesis-notes/${note.id}`);
      expect(history.changes).toHaveLength(1);
      expect(history.changes[0].price_review).toMatchObject({
        decision: "propose_change", anchor: {price: pin.anchor.price}, assumption: {id: assumption.id},
      });
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
