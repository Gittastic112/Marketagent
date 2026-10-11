import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { backendRequestHeaders, isSameOriginMutation, readBoundedBody, trustedBrowserOrigin } from "./request-security.ts";
import { createLocalLoginGuard } from "./local-login.ts";

const local = "http://localhost:3000";
test("only the configured browser origin may mutate, including port and scheme", () => {
  assert.equal(isSameOriginMutation(new Headers({ host: "localhost:3000", origin: local }), local), true);
  assert.equal(isSameOriginMutation(new Headers({ host: "127.0.0.1:3000", origin: "http://127.0.0.1:3000" }), local), true);
  for (const origin of ["null", "https://evil.test", "http://localhost:3001", "https://localhost:3000", ""]) {
    assert.equal(isSameOriginMutation(new Headers({ host: "localhost:3000", origin }), local), false);
  }
  assert.equal(trustedBrowserOrigin(new Headers({ host: "evil.test:3000", "x-forwarded-host": "localhost:3000" }), local), null);
});

test("backend forwarding uses a header allowlist, not browser credentials or attacker identity", () => {
  const headers = backendRequestHeaders(new Headers({ cookie: "test-cookie", authorization: "test-token",
    "x-market-intel-user": "forged", "x-market-intel-signature": "forged", "x-forwarded-for": "forged",
    "content-type": "application/json", accept: "application/json" }));
  assert.deepEqual([...headers.keys()], ["accept", "content-type"]);
  const proxy = readFileSync(new URL("../app/api/backend/[...path]/route.ts", import.meta.url), "utf8");
  assert.match(proxy, /redirect: "error"/);
  assert.match(proxy, /isSameOriginMutation/);
  assert.match(proxy, /readBoundedBody/);
});

test("body caps apply to declared and chunked bodies without trusting content length", async () => {
  assert.equal(new TextDecoder().decode(await readBoundedBody(new Request(local, { method: "POST", body: "1234" }), 4)), "1234");
  await assert.rejects(readBoundedBody(new Request(local, { method: "POST", body: "12345" }), 4), RangeError);
  await assert.rejects(readBoundedBody(new Request(local, { method: "POST", headers: { "content-length": "999" }, body: "1" }), 4), RangeError);
});

test("local password checks fail closed and attempts have a finite cooldown", () => {
  const check = createLocalLoginGuard(3, 100);
  assert.equal(check("test-user", "test-password", "test-user", "test-password", 100), true);
  assert.equal(check("wrong", "test-password", "test-user", "test-password", 101), false);
  assert.equal(check("test-user", "wrong", "test-user", "test-password", 102), false);
  assert.equal(check("test-user", "test-password", "test-user", "test-password", 103), false);
  assert.equal(check("test-user", "test-password", "test-user", "test-password", 200), true);
  assert.equal(check("test-user", "test-password", undefined, undefined, 201), false);
});
