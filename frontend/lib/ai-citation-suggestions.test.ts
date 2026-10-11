import assert from "node:assert/strict";
import test from "node:test";

import {
  applyCitationCandidate,
  applyManualCitationEdit,
  buildCitationValidationPayload,
} from "./ai-citation-suggestions.ts";


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
