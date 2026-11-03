import assert from "node:assert/strict";
import test from "node:test";
import { createLatestResource, createRequestGate } from "./latest-request.ts";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test("new request invalidates older completion tokens", () => {
  const gate = createRequestGate();
  const old = gate.begin();
  const current = gate.begin();
  assert.equal(old(), false);
  assert.equal(current(), true);
  gate.invalidate();
  assert.equal(current(), false);
});

test("out of order success cannot overwrite latest data", async () => {
  const resource = createLatestResource<string[]>();
  const old = deferred<string[]>();
  const first = resource.reload(() => old.promise);
  await resource.reload(async () => ["current"]);
  old.resolve(["obsolete"]);
  await first;
  assert.deepEqual(resource.getSnapshot().data, ["current"]);
});

test("late error cannot overwrite latest successful request", async () => {
  const resource = createLatestResource<string[]>();
  const old = deferred<string[]>();
  const first = resource.reload(() => old.promise);
  await resource.reload(async () => ["current"]);
  old.reject(new Error("obsolete failure"));
  await first;
  assert.equal(resource.getSnapshot().status, "ready");
  assert.equal(resource.getSnapshot().error, null);
});

test("refresh removes previously selectable evidence immediately", async () => {
  const resource = createLatestResource<string[]>();
  await resource.reload(async () => ["reviewed"]);
  const next = deferred<string[]>();
  const pending = resource.reload(() => next.promise);
  assert.equal(resource.getSnapshot().status, "loading");
  assert.equal(resource.getSnapshot().data, null);
  next.resolve([]);
  await pending;
  assert.deepEqual(resource.getSnapshot().data, []);
  assert.equal(resource.getSnapshot().status, "ready");
});

test("refresh failure stays unavailable and retry recovers", async () => {
  const resource = createLatestResource<string[]>();
  await resource.reload(async () => ["old"]);
  await assert.rejects(resource.reload(async () => { throw new Error("Offline"); }), /Offline/);
  assert.equal(resource.getSnapshot().status, "error");
  assert.equal(resource.getSnapshot().data, null);
  await resource.reload(async () => ["new"]);
  assert.equal(resource.getSnapshot().error, null);
  assert.deepEqual(resource.getSnapshot().data, ["new"]);
});

test("cleanup discards completion without notifying unmounted subscribers", async () => {
  const resource = createLatestResource<string[]>();
  let notifications = 0;
  const unsubscribe = resource.subscribe(() => notifications++);
  const next = deferred<string[]>();
  const pending = resource.reload(() => next.promise);
  unsubscribe();
  resource.cancel();
  next.resolve(["obsolete"]);
  await pending;
  assert.equal(notifications, 1);
  assert.equal(resource.getSnapshot().data, null);
});

test("cleanup permits Strict Mode effect replay to start a new request", async () => {
  const resource = createLatestResource<string[]>();
  const old = deferred<string[]>();
  const pending = resource.reload(() => old.promise);
  resource.cancel();
  await resource.reload(async () => ["replayed"]);
  old.resolve(["old"]);
  await pending;
  assert.deepEqual(resource.getSnapshot().data, ["replayed"]);
});

test("late success cannot erase current failure", async () => {
  const resource = createLatestResource<string[]>();
  const old = deferred<string[]>();
  const pending = resource.reload(() => old.promise);
  await assert.rejects(resource.reload(async () => { throw new Error("Current failure"); }));
  old.resolve(["old"]);
  await pending;
  assert.equal(resource.getSnapshot().error, "Current failure");
});

test("separate resource scopes do not share results", async () => {
  const companyA = createLatestResource<string[]>();
  const companyB = createLatestResource<string[]>();
  await companyA.reload(async () => ["company A"]);
  assert.equal(companyB.getSnapshot().data, null);
});

test("non-Error rejections receive a safe explicit error", async () => {
  const resource = createLatestResource<string[]>();
  await assert.rejects(resource.reload(async () => { throw null; }), /Request failed/);
  assert.equal(resource.getSnapshot().error, "Request failed");
});
