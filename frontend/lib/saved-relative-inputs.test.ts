import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { getSavedRelativeInputs, runSavedRelativeValuation } from "./api.ts";

const read = (path: string) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

test("saved input read preserves response metadata and zero values", async () => {
  const original = globalThis.fetch;
  let url = "";
  globalThis.fetch = (async (input: unknown) => {
    url = String(input);
    return new Response(JSON.stringify({ data: { financials: { cash: 0, debt: 0, ebitda: null } },
      meta: { is_stale: true, warnings: ["Review saved inputs"] }, errors: [] }), { status: 200 });
  }) as typeof fetch;
  try {
    const response = await getSavedRelativeInputs(12);
    assert.match(url, /\/api\/valuation\/relative\/assumptions\/12\/inputs$/);
    assert.equal(response.data?.financials.cash, 0);
    assert.equal(response.data?.financials.ebitda, null);
    assert.equal(response.meta.is_stale, true);
  } finally { globalThis.fetch = original; }
});

test("saved calculation posts the exact consent and snapshot without raw financials", async () => {
  const original = globalThis.fetch;
  let url = "";
  let posted: RequestInit | undefined;
  globalThis.fetch = (async (input: unknown, init?: RequestInit) => {
    url = String(input);
    posted = init;
    return new Response(JSON.stringify({ data: { relativeValues: [], inputBasis: { assumptionSetId: 12 } }, meta: {}, errors: [] }));
  }) as typeof fetch;
  try {
    const body = { country: "India", industryName: "Advertising", methods: ["pbv"],
      confirmInputBasis: true, inputBasisSha256: "a".repeat(64) };
    const response = await runSavedRelativeValuation(12, body);
    assert.match(url, /\/assumptions\/12\/run$/);
    assert.equal(posted?.method, "POST");
    assert.deepEqual(JSON.parse(String(posted?.body)), body);
    assert.equal(response.inputBasis?.assumptionSetId, 12);
  } finally { globalThis.fetch = original; }
});

test("snapshot conflict remains an actionable API error", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = (async () => new Response(JSON.stringify({ detail: "Saved input basis changed. Refresh and review." }),
    { status: 409 })) as typeof fetch;
  try {
    await assert.rejects(runSavedRelativeValuation(12, { peerSetId: 9, methods: ["pe"], confirmInputBasis: true,
      inputBasisSha256: "b".repeat(64) }), /Saved input basis changed/);
  } finally { globalThis.fetch = original; }
});

test("workspace consumes owned saved inputs instead of the EBITDA proxy adapter", () => {
  const source = read("components/advanced-workspace.tsx");
  assert.match(source, /<SavedRelativeValuation/);
  assert.match(source, /assumptionId=\{latestAssumptionSet.id\}/);
  assert.doesNotMatch(source, /Proxy for EBITDA/);
  assert.doesNotMatch(source, /bookEquity: undefined/);
});

test("saved input review preserves zero, gates consent, and uses server-side calculation", () => {
  const source = read("components/valuation/saved-relative-valuation.tsx");
  assert.match(source, /value \?\? undefined/);
  assert.match(source, /confirmedHash === basis.inputBasisSha256/);
  assert.match(source, /setConfirmedHash\(null\)/);
  assert.match(source, /runSavedRelativeValuation\(assumptionId/);
  assert.match(source, /inputBlockedReason=/);
  assert.match(source, /DataStateNotices/);
});

test("relative actions inside the DCF form never implicitly submit that form", () => {
  for (const path of ["components/valuation/relative-valuation-panel.tsx", "components/valuation/saved-relative-valuation.tsx"]) {
    const buttons = [...read(path).matchAll(/<button\b[^>]*>/g)];
    assert.ok(buttons.length > 0);
    for (const [button] of buttons) assert.match(button, /type="button"/);
  }
});

test("input disclosure shows provenance, currency, unavailable values, and unsaved boundary", () => {
  const source = read("components/valuation/relative-input-basis.tsx");
  for (const phrase of ["assumptionSetId", "savedAt", "updatedAt", "sourceFields", "claimType", "currency", "Not available", "Unsaved form edits are not used", "methodInputs"]) {
    assert.ok(source.includes(phrase), phrase);
  }
});

test("intermediate-width valuation navigation cannot overlap the output row", () => {
  const styles = read("app/globals.css");
  assert.match(styles, /@media \(max-width: 1500px\)\s*\{[^{}]*\.valuation-workspace-nav\s*\{\s*position: static;/);
  assert.match(styles, /\.relative-table-scroll\s*\{[^}]*overflow-x: auto;/);
});
