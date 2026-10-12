import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { backendData, signIn } from "./helpers";
import { verifyRoutes } from "./route-checks";

// Every record is isolated Mock Data. This audits rendered route states, not
// financial correctness or every control; functional workflows have separate tests.
async function detailRoutes(page: Page): Promise<Array<[string, string]>> {
  const companies = await backendData<Array<{ id: number; ticker: string }>>(page, "/companies");
  const company = companies.find(item => item.ticker === "E2EUSD")!;
  const comparisonCompany = companies.find(item => item.ticker === "BRIEFCMP")!;
  expect(company).toBeTruthy();
  expect(comparisonCompany).toBeTruthy();
  const models = await backendData<Array<{ id: number }>>(page, `/companies/${company.id}/valuation-models`);
  const portfolios = await backendData<Array<{ id: number; name: string }>>(page, "/portfolios");
  const portfolio = portfolios.find(item => item.name === "Mock Data Multi-Currency Portfolio")!;
  const documents = await backendData<Array<{ id: number; company_id: number; title: string }>>(page, "/raw-documents/summaries");
  let documentId = documents.find(item => item.company_id === company.id && item.title === "Mock Data route audit PDF")?.id;
  if (!documentId) {
    const response = await page.request.post(`/api/backend/api/companies/${company.id}/filings/pdf`, {
      headers: { origin: new URL(page.url()).origin },
      multipart: { document_type: "annual_report", title: "Mock Data route audit PDF", published_at: "2026-05-31T00:00:00Z",
        file: { name: "mock-route-audit.pdf", mimeType: "application/pdf",
          buffer: readFileSync(path.resolve(process.cwd(), "..", "backend", "tests", "fixtures", "financial_statement_table.pdf")) } },
    });
    const result = await response.json();
    expect(response.ok(), JSON.stringify(result)).toBe(true);
    documentId = result.data.raw_document_id;
  }
  type Candidate = { id: number; raw_document_id: number; source_page: number;
    source_locator_json: { page: number; page_width: number; page_height: number; coordinate_system: string; cell_bbox: Record<string, number> } };
  const candidates = await backendData<Candidate[]>(page, `/api/companies/${company.id}/financial-statements/extracted`);
  const candidate = candidates.find(item => item.raw_document_id === documentId && item.source_locator_json?.cell_bbox)!;
  expect(candidate).toBeTruthy();
  const event = await backendData<{ id: number }>(page, "/events", { method: "POST", data: {
    company_id: company.id, raw_document_id: documentId, event_type: "filing_update", information_speed: "slow",
    title: "Mock Data route audit event", description: "Mock Data: inspect the linked PDF before review.", event_time: "2026-07-20T12:00:00Z",
  } });
  const reference = await backendData<{ id: number }>(page, `/events/${event.id}/evidence-references`, { method: "POST", data: {
    raw_document_id: documentId, locator_type: "pdf_region", source_page: candidate.source_page, confidence_label: "low",
    bounding_box_json: { ...candidate.source_locator_json, bounding_box: candidate.source_locator_json.cell_bbox },
  } });
  const alert = await backendData<{ id: number }>(page, "/alerts", { method: "POST", data: {
    company_id: company.id, event_id: event.id, alert_type: "manual", title: "Mock Data route audit alert",
    summary: "Mock Data evidence pending review.",
  } });
  const thesis = await backendData<{ id: number }>(page, "/thesis-notes", { method: "POST", data: {
    company_id: company.id, title: "Mock Data route audit thesis", thesis_text: "Mock Data hypothesis requiring reviewed evidence.",
  } });
  const session = await backendData<{ id: number }>(page, "/research/sessions", { method: "POST", data: { title: "Mock Data route audit research" } });
  const comparison = await backendData<{ evidence_hash: string; sources: Array<{ id: number }>; reviews: Array<{ id: number; field: string; version: number }> }>(
    page, `/brief-sources/triage?company_id=${comparisonCompany.id}&include_mock=true`);
  const receipt = comparison.reviews.find(item => item.field === "starting_revenue") || await backendData<{ id: number }>(page, "/brief-sources/triage/reviews", {
    method: "POST", data: { company_id: comparisonCompany.id, field: "starting_revenue", include_mock: true,
      evidence_hash: comparison.evidence_hash, expected_version: 0, disposition: "investigate",
      notes: "Mock Data route audit only, not a review of genuine company evidence.", evidence_reviewed: true },
  });
  const companyPath = `/companies/${company.id}`;
  return [
    ...["", "/decisions", "/evidence", "/filings", "/fundamentals", "/setup", "/thesis", "/valuation", "/valuation/draft", "/valuation/peers"]
      .map(suffix => [`company${suffix.replaceAll("/", "-")}`, `${companyPath}${suffix}`] as [string, string]),
    ["saved-valuation", `${companyPath}/valuation/${models[0].id}`],
    ["alert-evidence", `/alerts/${alert.id}`],
    ["document-ai", `/documents/${documentId}/ai`],
    ["document-event", `/documents/${documentId}/event-evidence?evidence_reference=${reference.id}`],
    ["document-financial", `/documents/${documentId}/financial-evidence?candidate_id=${candidate.id}`],
    ["document-sections", `/documents/${documentId}/sections`],
    ["event-resolution", `/events/${event.id}/evidence-resolution`],
    ["portfolio-detail", `/portfolio/${portfolio.id}`],
    ["research-session", `/research/sessions/${session.id}`],
    ["thesis-detail", `/thesis-notes/${thesis.id}`],
    ["private-source", `/daily-brief/sources/${comparison.sources[0].id}`],
    ["private-receipt", `/daily-brief/triage/reviews/${receipt.id}`],
    // These core pages now contain the events, notes and partial brief produced
    // by the workflows above. Empty-page accessibility alone misses their states.
    ["populated-dashboard", "/"],
    ["populated-brief", "/daily-brief"],
    ["populated-thesis-notes", "/thesis-notes"],
  ];
}

for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
  test(`owned detail routes at ${viewport.width}px retain accessible evidence and bounded layouts`, async ({ page }, testInfo) => {
    await signIn(page);
    const routes = await detailRoutes(page);
    await verifyRoutes(page, testInfo, routes, viewport, "Isolated Mock Data detail records");
    const note = page.getByRole("row").filter({ has: page.getByRole("link", { name:"Mock Data route audit thesis", exact:true }) }).first();
    await expect(note.getByText("unreviewed", { exact:true })).toBeVisible();
    await expect(note.getByText("reviewed", { exact:true })).toHaveCount(0);
  });
}
