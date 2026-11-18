"use client";

import { useEffect, useId, useMemo, useState } from "react";
import { MAX_RESEARCH_JSON_BYTES } from "@/lib/research-lab-input";
import { createRequestGate } from "@/lib/latest-request";

export function ResearchJsonInput({ label, value, onChange, description, required = true, rows = 10 }: {
  label: string; value: string; onChange: (value: string) => void; description: string; required?: boolean; rows?: number;
}) {
  const id = useId();
  const requests = useMemo(createRequestGate, []);
  const [error, setError] = useState("");
  const [reading, setReading] = useState(false);
  useEffect(() => () => requests.invalidate(), [requests]);
  return <div className="field research-json-input">
    <label htmlFor={id}>{label}{required ? "" : " (optional)"}</label>
    <p id={`${id}-description`} className="basis-note">{description}</p>
    <textarea id={id} value={value} rows={rows} required={required} spellCheck={false} aria-describedby={`${id}-description`}
      onChange={event => { requests.invalidate(); setReading(false); setError(""); onChange(event.target.value); }} />
    <label htmlFor={`${id}-file`}>Load {label.toLowerCase()} from a JSON file</label>
    <input id={`${id}-file`} type="file" accept="application/json,.json" onChange={async event => {
      const file = event.target.files?.[0];
      const current = requests.begin();
      setError(""); setReading(false);
      if (!file) return;
      onChange("");
      if (file.size > MAX_RESEARCH_JSON_BYTES) { setError("JSON files are limited to 2 MiB."); return; }
      setReading(true);
      try { const text = await file.text(); if (current()) onChange(text); }
      catch { if (current()) setError("The selected JSON file could not be read."); }
      finally { if (current()) setReading(false); }
    }} />
    {reading && <p role="status">Reading JSON file…</p>}
    {error && <p role="alert">{error}</p>}
  </div>;
}
