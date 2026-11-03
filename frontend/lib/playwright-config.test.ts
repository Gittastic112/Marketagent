import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import ts from "typescript";

test("browser configuration neither reads private settings nor defaults to the normal app", () => {
  const source = readFileSync(new URL("../playwright.config.ts", import.meta.url), "utf8");
  const code = ts.transpileModule(source, {
    compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
  }).outputText;
  for (const env of [{}, {E2E_BASE_URL: "http://127.0.0.1:23000", E2E_BROWSER_CHANNEL: "chromium"}]) {
    const module = {exports: {} as {default?: {use: {baseURL: string; channel: string}}}};
    const require = (name: string) => {
      assert.equal(name, "@playwright/test", "Configuration must not import a settings-file reader");
      return {defineConfig: (config: unknown) => config};
    };
    const process = {env, loadEnvFile: () => {throw new Error("Private settings read");}};
    new Function("require", "module", "exports", "process", code)(require, module, module.exports, process);
    assert.equal(module.exports.default?.use.baseURL, env.E2E_BASE_URL || "http://127.0.0.1:13000");
    assert.equal(module.exports.default?.use.channel, env.E2E_BROWSER_CHANNEL || "chrome");
  }
});
