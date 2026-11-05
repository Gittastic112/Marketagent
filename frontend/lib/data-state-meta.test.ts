import assert from "node:assert/strict";
import { test } from "node:test";

import { buildDataStateBadges, summarizeApiMetas } from "./data-state-meta.ts";

test("successful stored data is available without asserting live freshness", () => {
  const badges = buildDataStateBadges({
    status: "success",
    source: "internal",
    last_updated: "2026-06-18T10:00:00Z",
    is_stale: false,
    is_mock: false,
    warnings: [],
    confidence: "high",
    processing_time_ms: 24
  });

  assert.deepEqual(badges, [
    { label: "Available", tone: "success" }
  ]);
});

test("buildDataStateBadges labels stale mock data and lower confidence", () => {
  const badges = buildDataStateBadges({
    status: "success",
    source: "internal",
    last_updated: "2026-06-18T10:00:00Z",
    is_stale: true,
    is_mock: true,
    warnings: [],
    confidence: "medium",
    processing_time_ms: null
  });

  assert.deepEqual(badges, [
    { label: "Stale", tone: "warning" },
    { label: "Mock Data", tone: "warning" },
    { label: "Medium confidence", tone: "muted" }
  ]);
});

test("buildDataStateBadges treats source mock as mock data for legacy envelopes", () => {
  const badges = buildDataStateBadges({
    status: "error",
    source: "mock",
    last_updated: null,
    is_stale: false,
    warnings: [],
    confidence: "low",
    processing_time_ms: null
  });

  assert.deepEqual(badges, [
    { label: "Error", tone: "danger" },
    { label: "Mock Data", tone: "warning" },
    { label: "Low confidence", tone: "muted" }
  ]);
});

test("buildDataStateBadges prioritizes request errors over legacy stale flags", () => {
  const badges = buildDataStateBadges({
    status: "error",
    source: "internal",
    last_updated: null,
    is_stale: true,
    warnings: ["The backend is unavailable"],
    confidence: "none",
    processing_time_ms: null
  });

  assert.deepEqual(badges, [
    { label: "Error", tone: "danger" }
  ]);
});

test("summarizeApiMetas reports stale and mock aggregate states", () => {
  const summary = summarizeApiMetas([
    {
      status: "success",
      source: "internal",
      last_updated: "2026-06-18T10:00:00Z",
      is_stale: true,
      is_mock: false,
      warnings: [],
      confidence: "high",
      processing_time_ms: null
    },
    {
      status: "success",
      source: "mock",
      last_updated: null,
      is_stale: false,
      warnings: [],
      confidence: "medium",
      processing_time_ms: null
    },
    null
  ]);

  assert.deepEqual(summary, {
    allStale: false,
    someStale: true,
    allUnavailable: false,
    someUnavailable: false,
    hasMock: true,
    hasManual: false,
    warnings: []
  });
});

test("summarizeApiMetas treats only real metadata entries as candidates", () => {
  const summary = summarizeApiMetas([null, undefined]);

  assert.deepEqual(summary, {
    allStale: false,
    someStale: false,
    allUnavailable: false,
    someUnavailable: false,
    hasMock: false,
    hasManual: false,
    warnings: []
  });
});

test("summarizeApiMetas separates unavailable requests from stale successful data", () => {
  const summary = summarizeApiMetas([
    {
      status: "error",
      source: "internal",
      last_updated: null,
      is_stale: true,
      warnings: ["The backend is unavailable"],
      confidence: "none",
      processing_time_ms: null
    },
    {
      status: "success",
      source: "internal",
      last_updated: "2026-06-18T10:00:00Z",
      is_stale: false,
      warnings: [],
      confidence: "high",
      processing_time_ms: 12
    }
  ]);

  assert.deepEqual(summary, {
    allStale: false,
    someStale: false,
    allUnavailable: false,
    someUnavailable: true,
    hasMock: false,
    hasManual: false,
    warnings: ["The backend is unavailable"]
  });
});

test("summarizeApiMetas reports all requests unavailable without calling them stale", () => {
  const summary = summarizeApiMetas([
    {
      status: "error",
      source: "internal",
      last_updated: null,
      is_stale: false,
      warnings: [],
      confidence: "none",
      processing_time_ms: null
    }
  ]);

  assert.equal(summary.allUnavailable, true);
  assert.equal(summary.someUnavailable, true);
  assert.equal(summary.allStale, false);
  assert.equal(summary.someStale, false);
});

test("manual inputs are a source label rather than a warning, and request timing is not a quality badge", () => {
  assert.deepEqual(buildDataStateBadges({ status: "success", source: "manual",
    last_updated: null, is_stale: false, warnings: [], confidence: "unknown", processing_time_ms: 12 }), [
    { label: "Available", tone: "success" }, { label: "Manual Data", tone: "muted" },
  ]);
});
