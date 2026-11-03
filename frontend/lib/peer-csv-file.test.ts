import assert from "node:assert/strict";
import test from "node:test";
import { MAXIMUM_PEER_CSV_BYTES, readPeerCsvFile } from "./peer-csv-file.ts";

function file(text: string, name = "peers.csv") {
  const bytes = new TextEncoder().encode(text);
  return { name, size: bytes.byteLength, arrayBuffer: async () => bytes.buffer as ArrayBuffer };
}

test("peer CSV reader preserves UTF-8 text, BOM and line endings", async () => {
  const text = "\ufeffname,notes\r\nIssuer,界\r\n";
  assert.equal(await readPeerCsvFile(file(text, "PEERS.CSV")), text);
});

test("peer CSV rejects other file types before reading", async () => {
  await assert.rejects(readPeerCsvFile({ ...file("x", "peers.xlsx"), arrayBuffer: async () => {
    assert.fail("must not read unsupported file");
  } }), /Select a .csv/);
});

test("peer CSV rejects empty files", async () => {
  await assert.rejects(readPeerCsvFile(file("")), /empty/);
});

test("peer CSV rejects oversized files before allocation", async () => {
  await assert.rejects(readPeerCsvFile({ name: "large.csv", size: MAXIMUM_PEER_CSV_BYTES + 1,
    arrayBuffer: async () => { assert.fail("must not read oversized file"); } }), /1 MB/);
});

test("peer CSV sanitizes file-read failures", async () => {
  await assert.rejects(readPeerCsvFile({ ...file("x"), arrayBuffer: async () => {
    throw new Error("PRIVATE_FILE_PATH");
  } }), /^Error: Could not read the CSV file/);
});

test("peer CSV rejects malformed UTF-8 instead of replacing bytes", async () => {
  await assert.rejects(readPeerCsvFile({ name: "invalid.csv", size: 2,
    arrayBuffer: async () => new Uint8Array([0xc3, 0x28]).buffer }), /UTF-8/);
});

test("peer CSV rejects NUL text", async () => {
  await assert.rejects(readPeerCsvFile(file("a\0b")), /NUL/);
});

test("peer CSV checks actual byte size after read", async () => {
  await assert.rejects(readPeerCsvFile({ name: "changed.csv", size: 1,
    arrayBuffer: async () => new ArrayBuffer(MAXIMUM_PEER_CSV_BYTES + 1) }), /1 MB/);
});
