export const MAX_RESEARCH_JSON_BYTES = 2 * 1024 * 1024;

export function parseResearchJson<T>(text: string, label: string, shape: "object" | "array"): T {
  if (!text.trim()) throw new Error(`${label} is required.`);
  if (new TextEncoder().encode(text).byteLength > MAX_RESEARCH_JSON_BYTES) throw new Error(`${label} exceeds the 2 MiB input limit.`);
  let value: unknown;
  try { value = JSON.parse(text); } catch { throw new Error(`${label} must be valid JSON. Decimal returns use 0.01 for 1%.`); }
  if (!value || typeof value !== "object" || (shape === "array" ? !Array.isArray(value) : Array.isArray(value))) {
    throw new Error(`${label} must be a JSON ${shape}.`);
  }
  // JSON permits overflowing numeric literals such as 1e999, which stringify to null.
  const pending: unknown[] = [value];
  while (pending.length) {
    const item = pending.pop();
    if (typeof item === "number" && !Number.isFinite(item)) throw new Error(`${label} contains a nonfinite number.`);
    if (item && typeof item === "object") for (const child of Object.values(item)) pending.push(child);
  }
  return value as T;
}

export function researchNumber(value: string, label: string): number {
  if (!value.trim()) throw new Error(`${label} is required.`);
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) throw new Error(`${label} must be finite.`);
  return parsed;
}

export function numericRecord(value: unknown): Record<string, number> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const entries = Object.entries(value);
  return entries.every(([, number]) => typeof number === "number" && Number.isFinite(number)) ? value as Record<string, number> : null;
}
