import assert from "node:assert/strict";
import test from "node:test";
import { parseResearchJson, researchNumber, numericRecord } from "./research-lab-input.ts";
import { createResearchRun, getResearchRun } from "./api/research-lab.ts";

test("research JSON preserves user data, rejects malformed shapes and nonfinite values", () => {
  const input = '{"source_label":"Unverified user input","returns":{"A":0,"B":-0.1}}';
  assert.deepEqual(parseResearchJson(input, "Dataset", "object"), JSON.parse(input));
  for (const invalid of ["", "null", "[]", '{"bad":NaN}', '{"bad":1e999}']) assert.throws(() => parseResearchJson(invalid, "Dataset", "object"));
  assert.throws(() => parseResearchJson("{}", "Returns", "array"));
  assert.equal(researchNumber("0", "Costs"), 0);
  assert.throws(() => researchNumber("", "Costs"));
  assert.equal(numericRecord({ A: null }), null);
});

test("research actions use registered endpoints and do not mutate holdings", async () => {
  const originalFetch = globalThis.fetch;
  const calls: Array<{ url: string; body: unknown }> = [];
  globalThis.fetch = (async (url, options) => {
    calls.push({ url: String(url), body: options?.body ? JSON.parse(String(options.body)) : null });
    return Response.json({ data: { run_id: 3, kind: "peers" }, meta: {}, errors: [] });
  }) as typeof fetch;
  try {
    await createResearchRun("peers", { country: "India", limit: 50 });
    await getResearchRun(3);
    assert.ok(calls[0].url.endsWith("/api/research-lab/peers"));
    assert.deepEqual(calls[0].body, { country: "India", limit: 50 });
    assert.ok(calls[1].url.endsWith("/api/research-lab/runs/3"));
  } finally { globalThis.fetch = originalFetch; }
});
