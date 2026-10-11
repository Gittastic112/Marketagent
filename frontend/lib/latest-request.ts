/** A token is valid only until another request starts or the scope is cleaned up. */
export function createRequestGate() {
  let revision = 0;
  return {
    begin() {
      const started = ++revision;
      return () => started === revision;
    },
    invalidate() { revision++; },
  };
}

export type ResourceSnapshot<T> = {
  status: "loading" | "ready" | "error";
  data: T | null;
  error: string | null;
  revision: number;
};

/** Read-only request state. Loading and failures never retain usable old evidence. */
export function createLatestResource<T>() {
  const gate = createRequestGate();
  const listeners = new Set<() => void>();
  let snapshot: ResourceSnapshot<T> = { status: "loading", data: null, error: null, revision: 0 };
  const publish = (next: ResourceSnapshot<T>) => {
    snapshot = next;
    listeners.forEach(listener => listener());
  };
  return {
    getSnapshot: () => snapshot,
    subscribe(listener: () => void) {
      listeners.add(listener);
      return () => { listeners.delete(listener); };
    },
    cancel: gate.invalidate,
    async reload(loader: () => Promise<T>) {
      const isCurrent = gate.begin();
      const revision = snapshot.revision + 1;
      publish({ status: "loading", data: null, error: null, revision });
      try {
        const data = await loader();
        if (isCurrent()) publish({ status: "ready", data, error: null, revision });
      } catch (error: unknown) {
        if (!isCurrent()) return;
        const message = error instanceof Error ? error.message : "Request failed";
        publish({ status: "error", data: null, error: message, revision });
        throw new Error(message);
      }
    },
  };
}
