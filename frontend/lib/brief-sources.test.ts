import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { analyzeBriefSource, listBriefSources, pasteBriefSource, searchBriefSources, setBriefSourceArchived, uploadBriefSource } from "./api/brief-sources.ts";

test("source search encodes literal terms and all filters through the shared transport", async () => {
  const original = globalThis.fetch;
  const calls: Array<{ url: URL; options: RequestInit | undefined }> = [];
  const page = { items: [], next_before_id: 12 };
  globalThis.fetch = (async (url, options) => {
    calls.push({ url: new URL(String(url)), options });
    return Response.json({ data: page, meta: {}, errors: [] });
  }) as typeof fetch;
  try {
    assert.deepEqual(await searchBriefSources({ q: "50% & margin / tax", company_id: 4, source_kind: "pdf",
      analysis_status: "failed", before_id: 19, limit: 10, lifecycle: "archived" }), page);
    assert.equal(calls[0].url.pathname, "/brief-sources/search");
    assert.deepEqual(Object.fromEntries(calls[0].url.searchParams), {
      q: "50% & margin / tax", company_id: "4", source_kind: "pdf", analysis_status: "failed", before_id: "19", limit: "10", lifecycle: "archived",
    });
    assert.equal(calls[0].options?.cache, "no-store");
    await searchBriefSources();
    assert.equal(calls[1].url.search, "");
    globalThis.fetch = (async () => Response.json({ errors: [{ message: "Search unavailable" }] }, { status: 503 })) as typeof fetch;
    await assert.rejects(searchBriefSources(), /Search unavailable/);
  } finally { globalThis.fetch = original; }
});

test("archive and restore send explicit intent and the viewed version, never source content", async () => {
  const original = globalThis.fetch;
  const calls: Array<{ url: string; options: RequestInit | undefined }> = [];
  globalThis.fetch = (async (url, options) => {
    calls.push({ url: String(url), options });
    return Response.json({ data: { id: 7 }, meta: {}, errors: [] });
  }) as typeof fetch;
  try {
    await setBriefSourceArchived(7, true, 1);
    await setBriefSourceArchived(7, false, 2);
    assert.ok(calls.every(call => call.url.endsWith("/brief-sources/7/lifecycle") && call.options?.method === "POST"));
    assert.deepEqual(calls.map(call => JSON.parse(String(call.options?.body))), [
      { archived: true, expected_version: 1 }, { archived: false, expected_version: 2 },
    ]);
    globalThis.fetch = (async () => Response.json({ errors: [{ message: "Source organization changed" }] }, { status: 409 })) as typeof fetch;
    await assert.rejects(setBriefSourceArchived(7, true, 1), /Source organization changed/);
  } finally { globalThis.fetch = original; }
});

test("private source helpers use the shared transport and an explicit AI disclosure", async () => {
  const original = globalThis.fetch;
  const calls: Array<{ url: string; options: RequestInit | undefined }> = [];
  globalThis.fetch = (async (url, options) => {
    calls.push({ url: String(url), options });
    return new Response(JSON.stringify({ data: { id: 7 }, meta: {}, errors: [] }), { status: 200 });
  }) as typeof fetch;
  try {
    await listBriefSources();
    await pasteBriefSource({ company_id: 4, title: "Earnings source", text: "Original source text", source_url: null, as_of_date: null });
    const form = new FormData(); form.set("title", "PDF source");
    await uploadBriefSource(form);
    await analyzeBriefSource(7, "v1");
    assert.ok(calls[0].url.endsWith("/brief-sources"));
    assert.equal(calls[2].options?.body, form);
    assert.equal(calls[2].options?.headers, undefined);
    assert.ok(calls[3].url.endsWith("/brief-sources/7/analyze"));
    assert.deepEqual(JSON.parse(String(calls[3].options?.body)), { privacy_disclosure_version: "v1" });
  } finally { globalThis.fetch = original; }
});

test("research UI preserves disclosure, source inspection and independent valuation review", () => {
  const inbox = readFileSync(new URL("../components/brief-source-inbox.tsx", import.meta.url), "utf8");
  const library = readFileSync(new URL("../components/brief-source-library.tsx", import.meta.url), "utf8");
  const findings = readFileSync(new URL("../components/brief-source-findings.tsx", import.meta.url), "utf8");
  const draft = readFileSync(new URL("../components/valuation/autofill-draft-review.tsx", import.meta.url), "utf8");
  assert.match(library, /disabled=\{!consent \|\| busy !== null\}/);
  assert.match(inbox, /does not send stored holdings, thesis notes or valuation values/);
  assert.match(library, /Inspect source text/);
  assert.match(findings, /Source match verified; interpretation not verified/);
  assert.match(findings, /No saved model or reviewed input was changed/);
  assert.doesNotMatch(inbox + library + findings, /updateValuationDraft|promoteValuationDraft|dangerouslySetInnerHTML/);
  assert.match(draft, /parent instanceof HTMLDetailsElement/);
  assert.match(draft, /removeEventListener\("hashchange"/);
});
