"use client";

import { RotateCcw } from "lucide-react";


export default function ErrorBoundary({ reset }: { reset: () => void }) {
  return (
    <section className="route-state" role="alert">
      <p className="eyebrow">Request failed</p>
      <h1>This workspace could not be loaded</h1>
      <p className="muted">The current view is unavailable. Your stored records were not changed.</p>
      <button type="button" onClick={reset}>
        <RotateCcw size={16} />
        Retry
      </button>
    </section>
  );
}
