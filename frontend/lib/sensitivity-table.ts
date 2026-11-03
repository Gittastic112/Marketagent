const record = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : null;

export function sensitivityAxis(value: unknown): number[] {
  if (!Array.isArray(value) || value.length > 25) return [];
  return [...new Set(value.filter((item): item is number => typeof item === "number" && Number.isFinite(item)))];
}

function numericKey(row: Record<string, unknown>, value: number): string | undefined {
  const wanted = Number(value.toFixed(4));
  const matches = Object.keys(row).filter(key => key.trim() !== "" && Number.isFinite(Number(key)) && Number(key) === wanted);
  // Ambiguous legacy keys must never select an arbitrary saved value.
  return matches.length === 1 ? matches[0] : undefined;
}

function matrixValue(matrix: unknown, x: number, y: number): unknown {
  const rows = record(matrix);
  if (!rows || !Number.isFinite(x) || !Number.isFinite(y)) return undefined;
  const yKey = numericKey(rows, y);
  const row = yKey === undefined ? null : record(rows[yKey]);
  if (!row) return undefined;
  const xKey = numericKey(row, x);
  return xKey === undefined ? undefined : row[xKey];
}

export function sensitivityCell(values: unknown, errors: unknown, x: number, y: number): { value: number | null; reason: string | null } {
  const value = matrixValue(values, x, y);
  if (typeof value === "number" && Number.isFinite(value)) return { value, reason: null };
  const reason = matrixValue(errors, x, y);
  return { value: null, reason: typeof reason === "string" && reason ? reason : "A valid saved calculation is not available for this cell." };
}

export function sensitivityMethod(axis: unknown): Record<string, unknown> | null {
  const method = record(record(axis)?.method);
  return method?.version === "fcff-sensitivity-v2" ? method : null;
}
