import assert from "node:assert/strict";
import test from "node:test";
import { snapshotReplayLabel } from "./portfolio-replay.ts";

test("legacy and incomplete snapshots cannot appear reconciled", () => {
  assert.equal(snapshotReplayLabel({ payload_json: null }), "Legacy history: replay unverified");
  assert.equal(snapshotReplayLabel({ payload_json: { replay_basis: { method: "future-method", status: "complete" } } }), "Legacy history: replay unverified");
  assert.equal(snapshotReplayLabel({ payload_json: { replay_basis: { method: "recorded-portfolio-replay-v1", status: "complete" } } }), "Incomplete recorded history");
  assert.equal(snapshotReplayLabel({ payload_json: { replay_basis: { method: "recorded-portfolio-replay-v1", status: "complete", input_sha256: "mock-input-hash", source_transaction_ids: [1] } } }), "Recorded activity reconciled");
});
