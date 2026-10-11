"use client";

import { usePeerSetManager } from "./use-peer-set";
import type { PeerSetManagerProps } from "./use-peer-set";
import { PeerSetManagerView } from "./peer-set-view";

export function PeerSetManager(props: PeerSetManagerProps) {
  return <PeerSetManagerSession key={props.companyId} {...props} />;
}

function PeerSetManagerSession(props: PeerSetManagerProps) {
  const state = usePeerSetManager(props);
  return <PeerSetManagerView {...state} />;
}
