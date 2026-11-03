export function receiptAuditCursor(value: string | string[] | undefined): number {
  if (typeof value !== "string" || !/^\d+$/.test(value)) return 0;
  const cursor = Number(value);
  return Number.isSafeInteger(cursor) && cursor >= 0 ? cursor : 0;
}

export function receiptAuditHref(afterId: number, audit?: string | null): string {
  const query = new URLSearchParams();
  if (audit && ["evidence", "coverage", "backfill"].includes(audit)) query.set("audit", audit);
  if (afterId > 0) query.set("peer_after", String(afterId));
  return `/data-health${query.size ? `?${query}` : ""}`;
}
