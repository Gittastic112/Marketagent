import type { PeerValuationSet } from "./api";

export function hasReadySelection(status: string, available: string[], selected: string): boolean {
  return status === "ready" && selected !== "" && available.includes(selected);
}

export function isPeerSetCalculationReady(peerSet: Pick<PeerValuationSet,
  "isActive" | "reviewStatus"> & Partial<Pick<PeerValuationSet,
  "reviewReceipt" | "calculationEligibility">>): boolean {
  return Boolean(peerSet.isActive && peerSet.reviewStatus === "reviewed"
    && peerSet.reviewReceipt?.matchesCurrentDiagnostics
    && peerSet.calculationEligibility?.canCalculate);
}
