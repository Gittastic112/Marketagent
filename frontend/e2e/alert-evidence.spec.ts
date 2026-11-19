import { expect, test } from "@playwright/test";

import { backendData, createCompany, signIn } from "./helpers";


test("alert review exposes complete and missing evidence states", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const evidenceQuote = "Gross margin increased by two percentage points.";
  const sourceText = `Management discussion\n${evidenceQuote}\nEnd of excerpt.`;
  const company = await createCompany(page, {
    ticker: `A${unique}`,
    local_symbol: `A${unique}`,
    name: "Alert Evidence E2E Fixture",
  });
  const source = await backendData<{ id: number }>(page, "/sources", {
    method: "POST",
    data: {
      name: `Evidence Source ${unique}`,
      source_type: "filing",
      base_url: "https://example.com",
      reliability_score: 90,
      active: true,
    },
  });
  const document = await backendData<{ id: number }>(page, "/raw-documents", {
    method: "POST",
    data: {
      company_id: company.id,
      source_id: source.id,
      document_type: "10-Q",
      title: `Evidence Filing ${unique}`,
      url: `https://example.com/filings/${unique}`,
      published_at: "2026-07-20T12:00:00Z",
      raw_text: sourceText,
      content_hash: `alert-evidence-${unique}`,
    },
  });
  const event = await backendData<{ id: number }>(page, "/events", {
    method: "POST",
    data: {
      company_id: company.id,
      raw_document_id: document.id,
      event_type: "filing_update",
      information_speed: "medium",
      title: "Margins changed",
      description: "Reported gross margin increased by two percentage points.",
      event_time: "2026-07-20T12:00:00Z",
      credibility_score: 92,
      priority_score: 78,
    },
  });
  const startChar = sourceText.indexOf(evidenceQuote);
  await backendData(page, `/events/${event.id}/evidence-references`, {
    method: "POST",
    data: {
      raw_document_id: document.id,
      locator_type: "text_span",
      start_char: startChar,
      end_char: startChar + evidenceQuote.length,
      quote: evidenceQuote,
      confidence_label: "high",
    },
  });
  const alert = await backendData<{ id: number }>(page, "/alerts", {
    method: "POST",
    data: {
      company_id: company.id,
      event_id: event.id,
      alert_type: "filing_alert",
      severity: "medium",
      title: `Review margin evidence ${unique}`,
      summary: "Margins changed in the latest filing.",
      why_it_matters: "The change may affect the operating-margin thesis.",
      what_changed: "Mock Data filing update",
      evidence: evidenceQuote,
      confidence_bucket: "high",
    },
  });

  await page.goto(`/alerts/${alert.id}`);
  await expect(page.getByRole("heading", { name: `Review margin evidence ${unique}` })).toBeVisible();
  await expect(page.getByRole("main").getByText("complete evidence", { exact: true })).toBeVisible();
  await expect(page.getByRole("main").getByText("Source Summary", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "View Evidence Trail" }).click();
  const evidenceDialog = page.getByRole("dialog");
  await expect(evidenceDialog).toBeVisible();
  await expect(evidenceDialog.getByText(`Evidence Source ${unique}`, { exact: true })).toBeVisible();
  await expect(evidenceDialog.getByText(`Evidence Filing ${unique}`, { exact: true })).toBeVisible();
  await expect(evidenceDialog.getByText(evidenceQuote, { exact: true })).toBeVisible();
  await expect(evidenceDialog.getByText("span-level locator", { exact: true })).toBeVisible();
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    const close = evidenceDialog.getByRole("button", { name: "Close", exact: true });
    await expect(close).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    expect(await evidenceDialog.evaluate(el => el.contains(el.ownerDocument.activeElement))).toBe(true);
    await page.keyboard.press("Tab");
    await expect(close).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("button", { name: "View Evidence Trail" })).toBeFocused();
    await page.keyboard.press("Enter");
  }
  await evidenceDialog.getByRole("button", { name: "Close" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);

  await page.goto("/alerts");
  const row = page.getByRole("row").filter({ hasText: `Review margin evidence ${unique}` });
  await row.getByText("Edit", { exact: true }).click();
  const edit = row.getByRole("form", { name: "Update alert" });
  await edit.getByLabel("Title").fill(`Reviewed title ${unique}`);
  await edit.getByRole("button", { name: "Save" }).click();
  await expect(page.getByRole("row").filter({hasText: `Reviewed title ${unique}` })).toBeVisible();
  const saved = await backendData<{evidence: string; what_changed: string; company_id: number; event_id: number}>(page, `/alerts/${alert.id}`);
  expect([saved.evidence, saved.what_changed, saved.company_id, saved.event_id]).toEqual([evidenceQuote, "Mock Data filing update", company.id, event.id]);

  const unlinkedAlert = await backendData<{ id: number }>(page, "/alerts", {
    method: "POST",
    data: {
      alert_type: "manual_alert",
      severity: "low",
      title: `Unlinked evidence ${unique}`,
      summary: "This alert has not been connected to an event.",
      confidence_bucket: "low",
    },
  });

  await page.goto(`/alerts/${unlinkedAlert.id}`);
  await expect(page.getByRole("main").getByText("missing evidence", { exact: true })).toBeVisible();
  await expect(page.getByRole("main").getByText("No source document is linked.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "View Evidence Trail" }).click();
  await expect(page.getByRole("dialog")).toContainText("No complete source chain is stored for this claim.");
});
