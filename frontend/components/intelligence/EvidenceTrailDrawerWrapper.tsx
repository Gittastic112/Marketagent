"use client";

import React, { useState } from "react";
import { EvidenceTrailDrawer } from "./EvidenceTrailDrawer";

interface EvidenceTrailDrawerWrapperProps {
  alertId?: number;
  eventId?: number;
}

export function EvidenceTrailDrawerWrapper({ alertId, eventId }: EvidenceTrailDrawerWrapperProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!alertId && !eventId) return null;

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="btn btn-outline"
        style={{ fontSize: "0.85rem", padding: "0.4rem 0.8rem", marginTop: "0.5rem" }}
        type="button"
      >
        View Evidence Trail
      </button>

      <EvidenceTrailDrawer
        alertId={alertId}
        eventId={eventId}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </>
  );
}
