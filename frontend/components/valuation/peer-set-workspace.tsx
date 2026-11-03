"use client";

import { useState } from "react";
import { PeerSetManager } from "@/components/valuation/peer-set-manager";
import { listPeerValuationSets, type PeerValuationSet } from "@/lib/api";

export function PeerSetWorkspace({ companyId, initialSets }: {
  companyId: number;
  initialSets: PeerValuationSet[];
}) {
  const [peerSets, setPeerSets] = useState(initialSets);
  return <PeerSetManager companyId={companyId} peerSets={peerSets} defaultOpen
    onChanged={async () => setPeerSets(await listPeerValuationSets(companyId, true))} />;
}
