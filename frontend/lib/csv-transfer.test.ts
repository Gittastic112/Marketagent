import assert from "node:assert/strict";
import test from "node:test";

import { unwrapCsvTransferResponse } from "./csv-transfer.ts";


test("CSV transfer adapter unwraps the API response envelope", () => {
  const result = unwrapCsvTransferResponse<{ imported_count: number }>({
    data: { imported_count: 2 },
    meta: {},
    errors: [],
  });

  assert.deepEqual(result, { imported_count: 2 });
});


test("CSV transfer adapter preserves legacy direct payloads", () => {
  const result = unwrapCsvTransferResponse<{ valid_count: number }>({
    valid_count: 3,
  });

  assert.deepEqual(result, { valid_count: 3 });
});


test("CSV transfer adapter rejects empty envelopes", () => {
  assert.throws(
    () => unwrapCsvTransferResponse({ data: null }),
    /did not include data/,
  );
});
