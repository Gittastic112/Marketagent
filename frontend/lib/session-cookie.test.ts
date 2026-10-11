import assert from "node:assert/strict";
import test from "node:test";

import { findNextAuthSessionToken } from "./session-cookie.ts";


test("findNextAuthSessionToken reads the standard local session cookie", () => {
  assert.equal(
    findNextAuthSessionToken([
      { name: "unrelated", value: "ignored" },
      { name: "next-auth.session-token", value: "local-token" },
    ]),
    "local-token",
  );
});


test("findNextAuthSessionToken reads secure session cookies", () => {
  assert.equal(
    findNextAuthSessionToken([
      { name: "__Secure-next-auth.session-token", value: "secure-token" },
    ]),
    "secure-token",
  );
});


test("findNextAuthSessionToken assembles numerically ordered cookie chunks", () => {
  assert.equal(
    findNextAuthSessionToken([
      { name: "next-auth.session-token.1", value: "middle" },
      { name: "next-auth.session-token.2", value: "end" },
      { name: "next-auth.session-token.0", value: "start" },
    ]),
    "startmiddleend",
  );
});


test("findNextAuthSessionToken returns null when no session cookie exists", () => {
  assert.equal(findNextAuthSessionToken([{ name: "other", value: "value" }]), null);
});
