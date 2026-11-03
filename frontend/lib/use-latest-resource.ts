"use client";

import { useCallback, useEffect, useMemo, useSyncExternalStore } from "react";
import { createLatestResource } from "./latest-request";

/** Keep loader stable with useCallback. A new loader creates a clean request scope. */
export function useLatestResource<T>(loader: () => Promise<T>) {
  const resource = useMemo(() => createLatestResource<T>(), [loader]);
  const snapshot = useSyncExternalStore(resource.subscribe, resource.getSnapshot, resource.getSnapshot);
  const reload = useCallback(() => resource.reload(loader), [resource, loader]);
  useEffect(() => {
    void reload().catch(() => { /* Failure is exposed by the snapshot. */ });
    return resource.cancel;
  }, [resource, reload]);
  return { ...snapshot, reload };
}
