import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import ts from "typescript";
import { ApiError } from "./api/contract.ts";

const root = fileURLToPath(new URL("../", import.meta.url));
type Call = { method: string; path: string; payload?: unknown };

// Execute the real action bodies and payload builders. Only Next's request
// boundary and the authenticated HTTP client are replaced in this unit test.
function actionHarness(reply: (call: Call) => unknown = () => ({ id: 17 })) {
  const calls: Call[] = [];
  const pages: string[] = [];
  const redirects: string[] = [];
  const cache = new Map<string, Record<string, any>>();
  const serverApi = Object.fromEntries(["Post", "Patch", "Delete", "Put"].map(method => [
    `server${method}Api`, async (url: string, payload?: unknown) => {
      const call = { method: method.toUpperCase(), path: url, payload };
      calls.push(call);
      return reply(call);
    },
  ]));
  function load(filename: string): Record<string, any> {
    const full = path.resolve(root, filename.replace(/\.ts$/, "") + ".ts");
    if (cache.has(full)) return cache.get(full)!;
    const module = { exports: {} as Record<string, any> };
    cache.set(full, module.exports);
    const compiled = ts.transpileModule(readFileSync(full, "utf8"), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    }).outputText;
    const require = (specifier: string) => {
      if (specifier === "next/cache") return { revalidatePath: (page: string) => pages.push(page) };
      if (specifier === "next/navigation") return { redirect: (url: string) => {
        redirects.push(url);
        throw new Error(`NEXT_REDIRECT:${url}`);
      } };
      if (specifier === "server-only") return {};
      if (specifier === "@/lib/server-api") return serverApi;
      if (["@/lib/api", "@/lib/api/contract"].includes(specifier)) return { ApiError };
      if (specifier.startsWith("@/")) return load(specifier.slice(2));
      if (specifier.startsWith(".")) return load(path.resolve(path.dirname(full), specifier));
      throw new Error(`Unexpected action dependency: ${specifier}`);
    };
    new Function("require", "module", "exports", compiled)(require, module, module.exports);
    return module.exports;
  }
  return { actions: load("app/actions"), load, calls, pages, redirects };
}

function form(values: Record<string, string | string[]>) {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) {
    for (const item of Array.isArray(value) ? value : [value]) data.append(key, item);
  }
  return data;
}

test("compatibility exports retain every action identity and domains cannot bypass authenticated HTTP", () => {
  const h = actionHarness();
  const expected = JSON.parse(readFileSync(new URL("./fixtures/server-action-exports.json", import.meta.url), "utf8"));
  assert.deepEqual(Object.keys(h.actions).sort(), expected);
  const facade = ts.createSourceFile("actions.ts", readFileSync(path.join(root, "app/actions.ts"), "utf8"), ts.ScriptTarget.Latest, true);
  assert.ok(facade.statements.every(ts.isExportDeclaration));
  for (const filename of readdirSync(path.join(root, "app/actions")).filter(name => name.endsWith(".ts"))) {
    const source = readFileSync(path.join(root, "app/actions", filename), "utf8");
    assert.doesNotMatch(source, /\bfetch\s*\(|from ["']@\/lib\/api["']/);
    assert.ok(source.split("\n").length < 450, filename);
    if (filename === "shared.ts") {
      assert.match(source, /^import "server-only"/);
      continue;
    }
    assert.match(source, /^"use server"/);
    for (const [name, action] of Object.entries(h.load(`app/actions/${filename}`))) {
      assert.equal(h.actions[name], action, `${filename}: ${name}`);
    }
  }
});

test("company creation sends normalized payload through the server client before redirecting", async () => {
  const h = actionHarness();
  await assert.rejects(h.actions.createCompanyWithState({ error: null }, form({ ticker: " aapl ", name: " Apple " })), /NEXT_REDIRECT:\/companies\/17/);
  assert.equal(h.calls.length, 1);
  assert.equal(h.calls[0].path, "/companies");
  assert.equal((h.calls[0].payload as any).ticker, "AAPL");
  assert.equal((h.calls[0].payload as any).name, "Apple");
  assert.deepEqual(h.pages, ["/", "/companies"]);
  assert.deepEqual(h.redirects, ["/companies/17"]);
});

test("rejected and expired authenticated saves do not revalidate or redirect", async () => {
  for (const status of [401, 403, 409, 422]) {
    const h = actionHarness(() => { throw new ApiError("Save rejected", status); });
    assert.deepEqual(await h.actions.createCompanyWithState({ error: null }, form({ ticker: "AAPL", name: "Apple" })), { error: "Save rejected" });
    assert.deepEqual(h.pages, []);
    assert.deepEqual(h.redirects, []);
  }
  const h = actionHarness(() => { throw new Error("private transport details"); });
  assert.deepEqual(await h.actions.deleteCompanyWithState({ error: null }, form({ id: "17" })), { error: "The request failed. Check the fields and try again." });
  assert.deepEqual(h.pages, []);
});

test("invalid IDs fail before any deletion or cache invalidation", async () => {
  const h = actionHarness();
  for (const id of ["", "0", "-2", "2.5", "oops"]) {
    assert.ok((await h.actions.deleteCompanyWithState({ error: null }, form({ id }))).error);
  }
  assert.deepEqual(h.calls, []);
  assert.deepEqual(h.pages, []);
});

test("evidence resolution retains exact whitespace, zero offsets and concurrency evidence", async () => {
  const h = actionHarness();
  await assert.rejects(h.actions.resolveEventEvidenceWithState({ error: null }, form({ event_id: "2", raw_document_id: "3", start_char: "0", end_char: "6", quote: " text ", search_query: " text ", occurrence_index: "1", document_content_hash: "abc" })), /NEXT_REDIRECT/);
  assert.deepEqual(h.calls[0], { method: "POST", path: "/events/2/evidence-resolution", payload: { raw_document_id: 3, start_char: 0, end_char: 6, quote: " text ", search_query: " text ", occurrence_index: 1, document_content_hash: "abc" } });
  assert.deepEqual(h.pages, ["/data-health", "/events/2/evidence-resolution", "/events", "/alerts"]);
});

test("AI actions require explicit disclosure acknowledgement before a request", async () => {
  const h = actionHarness();
  await assert.rejects(h.actions.triggerGenerateAiSummary(3, form({})), /acknowledge/);
  await assert.rejects(h.actions.triggerEventClassification(form({ event_id: "2", company_id: "3" })), /acknowledge/);
  assert.deepEqual(h.calls, []);
  await h.actions.triggerGenerateAiSummary(3, form({ privacy_disclosure_version: "v1" }));
  assert.deepEqual(h.calls[0], { method: "POST", path: "/raw-documents/3/ai-summary", payload: { privacy_disclosure_version: "v1" } });
});

test("schedule saves preserve disabled state and weekday zero", async () => {
  const h = actionHarness();
  assert.deepEqual(await h.actions.updateDailyBriefScheduleWithState({ error: null }, form({ timezone: " America/New_York ", local_time: "07:30", days_of_week: ["0", "4"] })), { error: null });
  assert.deepEqual(h.calls[0], { method: "PUT", path: "/daily-brief-schedule", payload: { enabled: false, timezone: "America/New_York", local_time: "07:30", days_of_week: [0, 4] } });
  assert.deepEqual(h.pages, ["/daily-brief"]);
});

test("valuation rename validates first and reports conflicts without invalidating a saved view", async () => {
  const h = actionHarness(() => { throw new ApiError("This model changed", 409); });
  assert.deepEqual(await h.actions.updateValuationModelWithState("4", "2", { error: null }, form({ name: " " })), { error: "Model name is required." });
  assert.deepEqual(h.calls, []);
  assert.deepEqual(await h.actions.updateValuationModelWithState("4", "2", { error: null }, form({ name: " New name " })), { error: "This model changed" });
  assert.deepEqual(h.calls[0], { method: "PATCH", path: "/valuation-models/4", payload: { name: "New name", description: null } });
  assert.deepEqual(h.pages, []);
});

test("draft promotion saves only edited fields and carries the newly saved version", async () => {
  const h = actionHarness(call => call.method === "PATCH" ? { updated_at: "v2" } : { id: 19 });
  const id = await h.actions.promoteValuationSetupDraft(form({ scenario: "base", name: "Reviewed draft", cash: "0", debt: "500", edited_field: ["cash"], reviewed_field: ["cash", "debt"], draft_updated_at: "v1" }), 7, "2");
  assert.equal(id, 19);
  assert.deepEqual(h.calls, [
    { method: "PATCH", path: "/valuation-drafts/7", payload: { assumptions_patch: { cash: 0 }, reviewed_fields: ["cash", "debt"], expected_updated_at: "v1" } },
    { method: "POST", path: "/valuation-drafts/7/promote", payload: { name: "Reviewed draft", description: null, model_type: "fcff_dcf", expected_updated_at: "v2" } },
  ]);
  assert.deepEqual(h.pages, ["/companies/2/valuation"]);
  const conflict = actionHarness(() => { throw new ApiError("Draft changed", 409); });
  await assert.rejects(conflict.actions.promoteValuationSetupDraft(form({ scenario: "base", draft_updated_at: "v1" }), 7, "2"), /Draft changed/);
  assert.equal(conflict.calls.length, 1);
  assert.deepEqual(conflict.pages, []);
});
