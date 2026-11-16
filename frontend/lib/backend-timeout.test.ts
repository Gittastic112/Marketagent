import assert from "node:assert/strict";
import test from "node:test";
import { backendTimeoutMs } from "./backend-timeout.ts";

test("explicit generation has a persistence margin while ordinary requests stay bounded", () => {
  assert.equal(backendTimeoutMs("POST", "research/sessions/12/messages"), 60_000);
  assert.equal(backendTimeoutMs("POST", "brief-sources/12/analyze"), 60_000);
  for (const [method, path] of [["GET", "research/sessions/12/messages"], ["POST", "research/sessions"],
    ["POST", "research/sessions/12/messages/extra"], ["GET", "companies"]]) {
    assert.equal(backendTimeoutMs(method, path), 15_000);
  }
});
