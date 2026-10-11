"use client";

import { useCallback, useState } from "react";
import { getSavedRelativeInputs, runSavedRelativeValuation, type RelativeValuationRequest } from "@/lib/api";
import { useLatestResource } from "@/lib/use-latest-resource";
import { DataStateNotices } from "@/components/ui/data-states";
import { RelativeInputBasis } from "./relative-input-basis";
import { RelativeValuationPanel } from "./relative-valuation-panel";

export function SavedRelativeValuation({ assumptionId }: { assumptionId: number }) {
  const loader = useCallback(() => getSavedRelativeInputs(assumptionId), [assumptionId]);
  const resource = useLatestResource(loader);
  const [confirmedHash, setConfirmedHash] = useState<string | null>(null);
  const basis = resource.data?.data;
  const refresh = () => {
    setConfirmedHash(null);
    void resource.reload().catch(() => {});
  };
  if (resource.status === "loading") return <p role="status">Loading saved valuation inputs...</p>;
  if (resource.status === "error" || !basis) return <div role="alert">
    <p>Saved valuation inputs unavailable. {resource.error}</p>
    <button type="button" onClick={refresh}>Retry saved inputs</button>
  </div>;

  const financials = Object.fromEntries(Object.entries(basis.financials).map(([key, value]) => [key, value ?? undefined]));
  const confirmed = confirmedHash === basis.inputBasisSha256;
  const run = (request: RelativeValuationRequest) => runSavedRelativeValuation(assumptionId, {
    country: request.country, industryName: request.industryName, peerSetId: request.peerSetId,
    methods: request.methods, confirmInputBasis: confirmed, inputBasisSha256: basis.inputBasisSha256,
  });
  return <>
    <DataStateNotices metas={resource.data?.meta ? [resource.data.meta] : []} />
    <RelativeInputBasis basis={basis} />
    <label className="relative-input-confirmation">
      <input type="checkbox" checked={confirmed} disabled={!basis.canCalculate}
        onChange={event => setConfirmedHash(event.target.checked ? basis.inputBasisSha256 : null)} />
      I reviewed these saved inputs, confirm matching currency and monetary/share scales, and accept the simplified debt/cash bridge.
    </label>
    <button type="button" onClick={refresh}>Refresh saved inputs</button>
    <RelativeValuationPanel key={basis.inputBasisSha256} companyId={String(basis.companyId)}
      financials={financials} runValuation={run}
      inputContextKey={basis.inputBasisSha256}
      inputBlockedReason={!basis.canCalculate ? "Correct the saved input blockers before calculating."
        : !confirmed ? "Review and confirm the saved input basis before calculating." : undefined} />
  </>;
}
