import assert from "node:assert/strict";
import { test } from "node:test";

import { parseFilingDiff } from "./filing-diff.ts";

test("parseFilingDiff preserves only generated add and remove semantics", () => {
  assert.deepEqual(
    parseFilingDiff(
      'Revenue <del class="diff-remove">100</del><ins class="diff-add">120</ins>',
    ),
    [
      { kind: "equal", text: "Revenue " },
      { kind: "remove", text: "100" },
      { kind: "add", text: "120" },
    ],
  );
});

test("parseFilingDiff keeps legacy untrusted markup as text", () => {
  const segments = parseFilingDiff(
    '<ins class="diff-add">&lt;img src=x onerror=&quot;alert(1)&quot;&gt;</ins><script>alert(2)</script>',
  );

  assert.deepEqual(segments, [
    { kind: "add", text: '<img src=x onerror="alert(1)">' },
    { kind: "equal", text: "<script>alert(2)</script>" },
  ]);
});
