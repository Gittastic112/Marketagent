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
      evidence: evidenceQuote,
      confidence_bucket: "high",
    },
  });

  await page.goto(`/alerts/${alert.id}`);
  await expect(page.getByRole("heading", { name: `Review margin evidence ${unique}` })).toBeVisible();
  await expect(page.getByText("complete evidence", { exact: true })).toBeVisible();
  await expect(page.getByText("Source Summary", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "View Evidence Trail" }).click();
  const evidenceDialog = page.getByRole("dialog");
  await expect(evidenceDialog).toBeVisible();
  await expect(evidenceDialog.getByText(`Evidence Source ${unique}`, { exact: true })).toBeVisible();
  await expect(evidenceDialog.getByText(`Evidence Filing ${unique}`, { exact: true })).toBeVisible();
  await expect(evidenceDialog.getByText(evidenceQuote, { exact: true })).toBeVisible();
  await expect(evidenceDialog.getByText("span-level locator", { exact: true })).toBeVisible();
  await evidenceDialog.getByRole("button", { name: "Close" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);

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
  await expect(page.getByText("missing evidence", { exact: true })).toBeVisible();
  await expect(page.getByText("No source document is linked.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "View Evidence Trail" }).click();
  await expect(page.getByRole("dialog")).toContainText("No complete source chain is stored for this claim.");
});
