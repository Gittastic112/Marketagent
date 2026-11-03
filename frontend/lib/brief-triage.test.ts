import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { fetchBriefTriage, fetchComparisonHistory, saveComparisonReview } from "./api/brief-triage.ts";
import { createLatestResource } from "./latest-request.ts";

test("comparison is a no-store GET with explicit company and Mock Data choice", async () => {
  const original = globalThis.fetch;
  const calls: Array<{ url: URL; options: RequestInit | undefined }> = [];
  globalThis.fetch = (async (url, options) => {
    calls.push({ url: new URL(String(url)), options });
    return Response.json({ data: { company_id: 7 }, meta: {}, errors: [] });
  }) as typeof fetch;
  try {
    assert.deepEqual(await fetchBriefTriage(7, false), { company_id: 7 });
    await fetchBriefTriage(8, true);
    assert.equal(calls[0].url.pathname, "/brief-sources/triage");
    assert.deepEqual(Object.fromEntries(calls[0].url.searchParams), { company_id: "7", include_mock: "false" });
    assert.deepEqual(Object.fromEntries(calls[1].url.searchParams), { company_id: "8", include_mock: "true" });
    assert.ok(calls.every(call => call.options?.cache === "no-store" && !call.options?.body));
    globalThis.fetch = (async () => Response.json({ errors: [{ message: "Comparison unavailable" }] }, { status: 503 })) as typeof fetch;
    await assert.rejects(fetchBriefTriage(7, false), /Comparison unavailable/);
  } finally { globalThis.fetch = original; }
});

test("changing comparison scope cannot publish late success or hide a current failure", async () => {
  const resource = createLatestResource<{ company_id: number }>();
  let finishOld!: (value: { company_id: number }) => void;
  const old = resource.reload(() => new Promise(resolve => { finishOld = resolve; }));
  await resource.reload(async () => ({ company_id: 8 }));
  finishOld({ company_id: 7 });
  await old;
  assert.equal(resource.getSnapshot().data?.company_id, 8);
  await assert.rejects(resource.reload(async () => { throw new Error("Unavailable"); }));
  assert.equal(resource.getSnapshot().data, null);
  assert.equal(resource.getSnapshot().status, "error");
});

test("comparison workspace keeps provenance, gaps and review-only links without mutation helpers", () => {
  const ui = readFileSync(new URL("../components/brief-source-triage.tsx", import.meta.url), "utf8");
  const page = readFileSync(new URL("../app/daily-brief/triage/page.tsx", import.meta.url), "utf8");
  assert.match(ui, /useLatestResource/);
  assert.match(ui, /key=\{`\$\{companyId\}:\$\{includeMock\}`\}/);
  assert.match(ui, /AI Interpretation/);
  assert.match(ui, /No detected opposition is not agreement/);
  assert.match(ui, /source\.as_of_date/);
  assert.match(ui, /source\.prompt_version/);
  assert.match(ui, /source\.input_hash/);
  assert.match(ui, /coverage\.not_examined/);
  assert.match(ui, /unmapped_findings/);
  assert.match(ui, /role="alert"/);
  assert.match(ui, /Refresh comparison/);
  assert.match(ui, /may initialize a review-required draft if none exists/);
  assert.match(page, /serverFetchApiResponse/);
  assert.doesNotMatch(ui + page, /analyzeBriefSource|postApi|patchApi|updateValuationDraft|dangerouslySetInnerHTML/);
});

test("review transport preserves evidence, owner-free scope and optimistic version", async () => {
  const original = globalThis.fetch;
  const calls: Array<{ url: URL; options: RequestInit | undefined }> = [];
  globalThis.fetch = (async (url, options) => {
    calls.push({ url: new URL(String(url)), options });
    return Response.json({ data: [], meta: {}, errors: [] });
  }) as typeof fetch;
  try {
    const body = { company_id: 7, field: "cash", include_mock: false, evidence_hash: "a".repeat(64),
      expected_version: 2, disposition: "investigate" as const, notes: "Review the exact cash scope", evidence_reviewed: true as const };
    await saveComparisonReview(body);
    assert.deepEqual(JSON.parse(String(calls[0].options?.body)), body);
    assert.equal(calls[0].url.pathname, "/brief-sources/triage/reviews");
    await fetchComparisonHistory(7, "cash", false, 12);
    assert.deepEqual(Object.fromEntries(calls[1].url.searchParams), { company_id: "7", field: "cash", include_mock: "false", limit: "20", before_id: "12" });
  } finally { globalThis.fetch = original; }
});

test("review UI has explicit confirmation, historical evidence and no financial mutation", () => {
  const ui = readFileSync(new URL("../components/brief-comparison-review.tsx", import.meta.url), "utf8");
  const receipt = readFileSync(new URL("../app/daily-brief/triage/reviews/[id]/page.tsx", import.meta.url), "utf8");
  assert.match(ui, /evidence_reviewed: true/);
  assert.match(ui, /expected_version: latest\?\.version \?\? 0/);
  assert.match(ui, /setBlocked\(true\)/);
  assert.match(ui, /User Assumption/);
  assert.match(ui, /Mock-inclusive scope/);
  assert.match(receipt, /Evidence has changed/);
  assert.doesNotMatch(ui + receipt, /dangerouslySetInnerHTML|updateValuationDraft|promoteValuationDraft|analyzeBriefSource/);
});
