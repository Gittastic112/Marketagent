import assert from "node:assert/strict";
import test from "node:test";

import {
  applyCitationCandidate,
  applyManualCitationEdit,
  buildCitationValidationPayload,
  readableCitations,
  readableEvaluation,
} from "./ai-citation-suggestions.ts";

test("claim flags remain review guidance and malformed diagnostic fields do not crash", () => {
  const result = readableEvaluation({evaluation_json: {passed: true, checks: {citations_valid: true}, claim_review: {
    requires_review_notes: true, claims: [null, {flags: [false]}, {source_id: "raw_document:7", claim_text: "Mock Data 21%",
      flags: [{code: "numeric_literals_unmatched", message: "Review the amount."}]}],
  }}});
  assert.equal(result.passed, true);
  assert.equal(result.requiresReviewNotes, true);
  assert.equal(result.claimFlags.length, 1);
  assert.equal(result.claimFlags[0].claimText, "Mock Data 21%");
  assert.equal(readableEvaluation({evaluation_json: {claim_review: []}}).requiresReviewNotes, false);
});

test("legacy metadata cannot crash citations or approve an unverified evaluation", () => {
  const [citation] = readableCitations({citations_json: [{quote: {html: "untrusted"}, source_id: 7, internal_href: "//example.invalid", start_char: -1}]});
  assert.equal(citation.quote, "");
  assert.equal(citation.internal_href, null);
  assert.equal(citation.status, "not_evaluated");
  assert.equal(citation.start_char, undefined);
  for (const evaluation_json of [null, {}, {passed: "true", checks: {citations: true}}, {passed: true}, {passed: true, checks: {citations: "yes"}}, {passed: true, checks: {citations: false}}]) {
    assert.equal(readableEvaluation({evaluation_json}).passed, false);
  }
  assert.equal(readableEvaluation({evaluation_json: {passed: true, checks: {citations: true, citations_required: false}}}).passed, true);
});


test("applying a suggested passage preserves exact source offsets", () => {
  const drafts = applyCitationCandidate({}, "raw_document:7", {
    quote: "Revenue increased 12% year over year.",
    start_char: 40,
    end_char: 79,
    score: 1,
    confidence: "high",
    matched_terms: ["revenue", "12%"],
    claim_term_count: 5,
    matched_term_count: 5,
    internal_href: "/documents/7/sections",
  });

  assert.deepEqual(buildCitationValidationPayload(["raw_document:7"], drafts), {
    citations: [{
      source_id: "raw_document:7",
      quote: "Revenue increased 12% year over year.",
      start_char: 40,
      end_char: 79,
    }],
  });
});


test("manual edits discard stale offsets and missing sources block validation", () => {
  const edited = applyManualCitationEdit(
    { "raw_document:7": { quote: "Old quote", start_char: 1, end_char: 10 } },
    "raw_document:7",
    "Reviewed exact quote",
  );

  assert.deepEqual(buildCitationValidationPayload(["raw_document:7"], edited), {
    citations: [{ source_id: "raw_document:7", quote: "Reviewed exact quote" }],
  });
  assert.equal(
    buildCitationValidationPayload(["raw_document:7", "raw_document:8"], edited),
    null,
  );
});
