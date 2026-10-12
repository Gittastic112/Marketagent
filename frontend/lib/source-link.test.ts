import assert from "node:assert/strict";
import test from "node:test";
import { sourceLink } from "./source-link.ts";

test("legacy stored citations cannot become executable or credential-bearing links", () => {
  for (const value of ["javascript:alert(1)", "data:text/html,test", "file:///etc/passwd", "//example.com",
    "https://user:secret@example.com", "https://example.com\\@evil.test", "https://example.com\n"]) {
    assert.equal(sourceLink(value), null);
  }
  assert.equal(sourceLink("https://example.com/report.pdf#page=14"), "https://example.com/report.pdf#page=14");
});
