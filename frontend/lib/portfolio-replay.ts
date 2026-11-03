import type { PortfolioSnapshot } from "./api/portfolio";

export function snapshotReplayLabel(snapshot: Pick<PortfolioSnapshot, "payload_json">): string {
  const basis = snapshot.payload_json?.replay_basis;
  if (!basis || typeof basis !== "object" || !("method" in basis) || basis.method !== "recorded-portfolio-replay-v1") {
    return "Legacy history: replay unverified";
  }
  if ("status" in basis && basis.status === "complete" && "input_sha256" in basis && basis.input_sha256
    && "source_transaction_ids" in basis && Array.isArray(basis.source_transaction_ids) && basis.source_transaction_ids.length > 0) {
    return "Recorded activity reconciled";
  }
  return "Incomplete recorded history";
}
