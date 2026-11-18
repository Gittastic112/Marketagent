import assert from "node:assert/strict";
import test from "node:test";
import type { ValuationAIEvidence, ValuationMemoResponse } from "./api/ai.ts";
import { memoBasisError, memoLink, memoSessionKey, valuationMemoExport } from "./valuation-memo.ts";

const selected = { valuationId: 7, assumptionSetId: 11, scenario: "Base", assumptionsUpdatedAt: "2026-11-17T10:00:00Z", outputId: 19 };
const evidence: ValuationAIEvidence = {
  valuation_model_id: 7, assumption_set_id: 11, scenario: "Base", assumptions_updated_at: selected.assumptionsUpdatedAt,
  output_id: 19, ai_output_id: 42, claim_type: "AI Interpretation", is_current: false, basis_verified: true,
  provider_name: "fixture", model_name: "Mock Data", prompt_version: "test", input_hash: "a".repeat(64),
  source_ids: ["valuation:7", "dcf_assumption_set:11"], generated_at: selected.assumptionsUpdatedAt,
  review_status: "pending", is_mock: true, confidence_label: "not_evaluated", limitations: null,
  interpretation_quality: "not_evaluated",
};
const memo: ValuationMemoResponse = { memo_markdown: "# Thesis\n\n| Input | Value |\n| --- | --- |\n| WACC | 9% |", evidence };

test("memo response identity rejects another model, scenario, saved update or calculation", () => {
  assert.equal(memoBasisError(memo, selected), null);
  assert.equal(memoBasisError({ ...memo, evidence: { ...evidence, assumptions_updated_at: "2026-11-17T10:00:00+00:00" } }, selected), null);
  for (const changed of [{ valuationId: 8 }, { assumptionSetId: 12 }, { scenario: "Bear" },
    { assumptionsUpdatedAt: "2026-11-18T10:00:00Z" }, { outputId: 20 }]) {
    assert.ok(memoBasisError(memo, { ...selected, ...changed }));
    assert.notEqual(memoSessionKey(selected), memoSessionKey({ ...selected, ...changed }));
  }
});

test("memo links resolve only declared references or safe external URLs", () => {
  const ids = evidence.source_ids;
  assert.equal(memoLink("source_id:valuation:7", ids, "memo-42"), "#memo-42-source-1");
  assert.equal(memoLink("#memo-42-source-2", ids, "memo-42"), "#memo-42-source-2");
  assert.equal(memoLink("https://www.sec.gov/report#page=12", ids, "memo-42"), "https://www.sec.gov/report#page=12");
  for (const href of ["source_id:valuation:99", "#memo-42-source-3", "/companies/99", "//evil.test", "javascript:alert(1)",
    "data:text/html,test", "mailto:test@example.com", "https://user:secret@example.com", "https://example.com\\evil"]) {
    assert.equal(memoLink(href, ids, "memo-42"), null, href);
  }
});

test("Markdown export retains original text and exact artifact evidence, including historical status", () => {
  const exported = valuationMemoExport(memo);
  assert.equal(exported.filename, "valuation-7-assumptions-11-memo-42.md");
  assert.equal(exported.mimeType, "text/markdown;charset=utf-8");
  assert.ok(exported.content.includes(memo.memo_markdown!));
  assert.ok(exported.content.includes('"is_current": false'));
  assert.ok(exported.content.includes('"review_status": "pending"'));
  assert.ok(exported.content.includes("Mock Data"));
});

test("legacy memo export does not invent saved identity", () => {
  const legacy = { memo_markdown: "Legacy memo", ai_output_id: 3 };
  assert.equal(memoBasisError(legacy, selected), null);
  assert.equal(valuationMemoExport(legacy).filename, "valuation-unverified-assumptions-unverified-memo-3.md");
  assert.ok(valuationMemoExport(legacy).content.includes("legacy_unverified"));
});
