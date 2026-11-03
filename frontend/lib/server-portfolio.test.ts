import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import ts from "typescript";
import { errorResponse } from "./api/contract.ts";

test("portfolio valuation reads bound concurrent requests, preserve order and retain failures", async () => {
  let active = 0;
  let peak = 0;
  const requested: number[] = [];
  const failure = errorResponse("NETWORK_ERROR", "Stored values temporarily unavailable");
  const module = { exports: {} as Record<string, any> };
  const code = ts.transpileModule(readFileSync(new URL("./server-portfolio.ts", import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const require = (name: string) => {
    if (name === "server-only") return {};
    if (name === "@/lib/server-api") return { serverFetchApiResponse: async (url: string) => {
      const id = Number(url.split("/")[2]);
      requested.push(id);
      peak = Math.max(peak, ++active);
      await new Promise(resolve => setTimeout(resolve, id % 3));
      active--;
      return id === 6 ? failure : { data: { portfolio_id:id }, meta: { status:"success" }, errors:[] };
    } };
    throw new Error(`Unexpected dependency: ${name}`);
  };
  new Function("require", "module", "exports", code)(require, module, module.exports);
  const portfolios = Array.from({length:33}, (_, index) => ({id:index + 1}));
  const responses = await module.exports.loadPortfolioValuations(portfolios);
  assert.equal(peak, 4);
  assert.equal(active, 0);
  assert.deepEqual(requested, portfolios.map(row => row.id));
  assert.equal(responses.length, 33);
  assert.equal(responses[5], failure);
  assert.deepEqual(responses.filter((_:unknown, index:number) => index !== 5).map((row:any) => row.data.portfolio_id),
    portfolios.filter(row => row.id !== 6).map(row => row.id));
  assert.deepEqual(await module.exports.loadPortfolioValuations([]), []);
});
