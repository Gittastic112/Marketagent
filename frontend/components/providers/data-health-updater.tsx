"use client";

import { useEffect } from "react";
import { useDataHealth } from "./data-health-provider";

export function DataHealthUpdater({ segment, isStale }: { segment: string; isStale: boolean }) {
  const health = useDataHealth();

  useEffect(() => {
    if (health) {
      health.setStaleSegment(segment, isStale);
    }
  }, [segment, isStale, health]);

  return null;
}
