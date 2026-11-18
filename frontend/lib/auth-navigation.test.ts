import assert from "node:assert/strict";
import test from "node:test";
import { localCallback } from "./auth-navigation.ts";

test("callbacks remain local after URL and escape normalization", () => {
  const origin = "http://localhost:3000";
  for (const value of [null, "//evil.invalid/path", "https://evil.invalid", "/\\evil.invalid",
    "\\\\evil.invalid", " /companies", "javascript:alert(1)", "/%2f%2fevil.invalid", "/%5cevil.invalid",
    "http://user@localhost:3000/private", "http://localhost:3001", "/bad%", "/\nevil.invalid"]) {
    assert.equal(localCallback(value, origin), "/", String(value));
  }
  assert.equal(localCallback("/companies/4?tab=thesis#evidence", origin), "/companies/4?tab=thesis#evidence");
  assert.equal(localCallback(`${origin}/daily-brief`, origin), "/daily-brief");
});
