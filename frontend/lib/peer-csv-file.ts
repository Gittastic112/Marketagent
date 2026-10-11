export const MAXIMUM_PEER_CSV_BYTES = 1_000_000;

type CsvFile = Pick<File, "name" | "size" | "arrayBuffer">;

export async function readPeerCsvFile(file: CsvFile): Promise<string> {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    throw new Error("Select a .csv file using the published peer template.");
  }
  if (file.size === 0) throw new Error("The CSV file is empty.");
  if (file.size > MAXIMUM_PEER_CSV_BYTES) throw new Error("CSV exceeds the 1 MB limit.");
  let bytes: ArrayBuffer;
  try {
    bytes = await file.arrayBuffer();
  } catch {
    throw new Error("Could not read the CSV file. Select it again.");
  }
  if (!bytes.byteLength) throw new Error("The CSV file is empty.");
  if (bytes.byteLength > MAXIMUM_PEER_CSV_BYTES) throw new Error("CSV exceeds the 1 MB limit.");
  let text: string;
  try {
    // Preserve a UTF-8 BOM so preview hashes the exact decoded file content.
    text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
  } catch {
    throw new Error("CSV must be UTF-8 encoded. Export it as UTF-8 CSV and retry.");
  }
  if (text.includes("\0")) throw new Error("CSV must not contain NUL bytes.");
  return text;
}
