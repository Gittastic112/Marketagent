"use client";

import { useEffect, useMemo, useState } from "react";
import { createRequestGate } from "@/lib/latest-request";
import { TextField } from "@/components/form-fields";
import {
  BottomUpMacroSegment,
  MacroSensitivityResult,
  runBottomUpMacroSensitivity,
  runTopDownMacroSensitivity,
  TopDownMacroPeriod,
} from "@/lib/api";

type Props = {
  market: string;
  country: string;
};

export function MacroSensitivityPanel({ market, country }: Props) {
  const [mode, setMode] = useState<"top_down" | "bottom_up">("bottom_up");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MacroSensitivityResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const gate = useMemo(createRequestGate, [market, country]);
  useEffect(() => () => gate.invalidate(), [gate]);
  const invalidate = () => { gate.invalidate(); setResult(null); setError(null); setLoading(false); };

  // Bottom Up State
  const [segments, setSegments] = useState<BottomUpMacroSegment[]>([
    { segment_name: "", sic_code: "", segment_weight: null },
    { segment_name: "", sic_code: "", segment_weight: null },
  ]);

  // Top Down State
  const [periods, setPeriods] = useState<TopDownMacroPeriod[]>([
    { period_label: "" },
    { period_label: "" },
    { period_label: "" },
  ]);

  const handleRunBottomUp = async () => {
    const current = gate.begin();
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const validSegments = segments.filter(
        (segment) => segment.segment_name && segment.sic_code && (segment.segment_weight ?? 0) > 0,
      );
      if (validSegments.length === 0) {
        throw new Error("Add at least one segment with a name, SIC code, and positive weight.");
      }
      const res = await runBottomUpMacroSensitivity({
        market,
        country,
        segments: validSegments,
      });
      if (current()) setResult(res);
    } catch (err: unknown) {
      if (current()) setError(err instanceof Error ? err.message : "Failed to run calculation");
    } finally {
      if (current()) setLoading(false);
    }
  };

  const handleRunTopDown = async () => {
    const current = gate.begin();
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const complete = periods.every((period) =>
        period.period_label
        && period.operating_income != null
        && period.market_cap != null
        && period.total_debt != null
        && period.change_in_long_term_bond_rate != null
        && period.gdp_growth != null
        && period.inflation_change != null
        && period.currency_change != null
      );
      if (!complete) {
        throw new Error("Complete all fields for at least three historical periods.");
      }
      const res = await runTopDownMacroSensitivity({
        frequency: "annual",
        periods,
      });
      if (current()) setResult(res);
    } catch (err: unknown) {
      if (current()) setError(err instanceof Error ? err.message : "Failed to run regression");
    } finally {
      if (current()) setLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-4 space-y-4" style={{ background: "var(--panel-bg)", borderColor: "var(--line)", color: "var(--text)" }} onChange={invalidate}>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "start", gap: "12px" }}>
        <h3 className="text-lg font-semibold" style={{ flex: "1 1 12rem" }}>Macro Sensitivity Engine</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "8px", flex: "1 1 20rem" }}>
          <button
            type="button"
            onClick={() => { invalidate(); setMode("bottom_up"); }}
            aria-pressed={mode === "bottom_up"}
            className={mode === "bottom_up" ? "primary-button" : "secondary-button"}
            style={{ minWidth: 0, whiteSpace: "normal" }}
          >
            Bottom-Up (Segments)
          </button>
          <button
            type="button"
            onClick={() => { invalidate(); setMode("top_down"); }}
            aria-pressed={mode === "top_down"}
            className={mode === "top_down" ? "primary-button" : "secondary-button"}
            style={{ minWidth: 0, whiteSpace: "normal" }}
          >
            Top-Down (Regression)
          </button>
        </div>
      </div>

      {mode === "bottom_up" ? (
        <div className="space-y-4">
          <div className="border rounded p-2 space-y-2" style={{ background: "var(--panel-bg)", borderColor: "var(--line)" }}>
            {segments.map((seg, idx) => (
              <fieldset key={idx} style={{ minWidth: 0, border: 0, padding: "8px" }}>
                <legend>Segment {idx + 1}</legend>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 9rem), 1fr))", gap: "8px" }}>
                <TextField
                  id={`macro-segment-name-${idx + 1}`}
                  label={`Segment name ${idx + 1}`}
                  type="text"
                  value={seg.segment_name}
                  onChange={(e) => {
                    const newSegs = [...segments];
                    newSegs[idx].segment_name = e.target.value;
                    setSegments(newSegs);
                  }}
                />
                <TextField
                  id={`macro-segment-sic-${idx + 1}`}
                  label={`SIC code ${idx + 1}`}
                  type="text"
                  value={seg.sic_code || ""}
                  onChange={(e) => {
                    const newSegs = [...segments];
                    newSegs[idx].sic_code = e.target.value;
                    setSegments(newSegs);
                  }}
                  placeholder="e.g. 7372"
                />
                <TextField
                  id={`macro-segment-weight-${idx + 1}`}
                  label={`Segment weight ${idx + 1} (0–1)`}
                  type="number"
                  step="0.1"
                  value={seg.segment_weight ?? ""}
                  onChange={(e) => {
                    const newSegs = [...segments];
                    newSegs[idx].segment_weight = e.target.value === "" ? null : Number(e.target.value);
                    setSegments(newSegs);
                  }}
                />
                </div>
              </fieldset>
            ))}
          </div>
          <button
            type="button"
            onClick={handleRunBottomUp}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            {loading ? "Calculating..." : "Run Bottom-Up Calculation"}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="border rounded p-2 space-y-2" style={{ background: "var(--panel-bg)", borderColor: "var(--line)" }}>
            {periods.map((p, idx) => (
              <fieldset key={idx} style={{ minWidth: 0, border: 0, padding: "8px" }}>
                <legend>Historical period {idx + 1}</legend>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 9rem), 1fr))", gap: "8px" }}>
                  <TextField
                    id={`macro-period-${idx + 1}`}
                    label={`Period ${idx + 1}`}
                    type="text"
                    value={p.period_label}
                    onChange={(e) => {
                      const newPeriods = [...periods];
                      newPeriods[idx].period_label = e.target.value;
                      setPeriods(newPeriods);
                    }}
                  />
                  {(["operating_income", "market_cap", "total_debt"] as const).map((field) => (
                    <TextField
                      id={`macro-${field}-${idx + 1}`}
                      label={`${field.replaceAll("_", " ")} ${idx + 1}`}
                      key={field}
                      onChange={(e) => {
                        const newPeriods = [...periods];
                        newPeriods[idx][field] = e.target.value === "" ? null : Number(e.target.value);
                        setPeriods(newPeriods);
                      }}
                      step="0.01"
                      type="number"
                      value={p[field] ?? ""}
                    />
                  ))}
                  {([
                    ["change_in_long_term_bond_rate", "Rate change"],
                    ["gdp_growth", "GDP growth"],
                    ["inflation_change", "Inflation change"],
                    ["currency_change", "Currency change"],
                  ] as const).map(([field, label]) => (
                    <TextField
                      id={`macro-${field}-${idx + 1}`}
                      label={`${label} ${idx + 1}`}
                      key={field}
                      onChange={(e) => {
                        const newPeriods = [...periods];
                        newPeriods[idx][field] = e.target.value === "" ? null : Number(e.target.value);
                        setPeriods(newPeriods);
                      }}
                      step="0.0001"
                      type="number"
                      value={p[field] ?? ""}
                    />
                  ))}
                </div>
              </fieldset>
            ))}
          </div>
          <button
            type="button"
            onClick={handleRunTopDown}
            disabled={loading}
            className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            {loading ? "Running Regression..." : "Run Top-Down Regression"}
          </button>
        </div>
      )}

      {error && <div role="alert" className="form-error">{error}</div>}

      {result && (
        <div className="mt-6 border-t border-neutral-800 pt-4">
          <h4 className="text-md font-semibold mb-4">Results ({result.method})</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded" style={{ background: "var(--panel-bg-alt)" }}>
              <div className="text-xs text-neutral-500 mb-1">Duration</div>
              <div className="text-xl">{result.firm_value?.duration?.toFixed(2) ?? "N/A"}</div>
            </div>
            <div className="p-3 rounded" style={{ background: "var(--panel-bg-alt)" }}>
              <div className="text-xs text-neutral-500 mb-1">Cyclicality</div>
              <div className="text-xl">{result.firm_value?.cyclicality?.toFixed(2) ?? "N/A"}</div>
            </div>
            <div className="p-3 rounded" style={{ background: "var(--panel-bg-alt)" }}>
              <div className="text-xs text-neutral-500 mb-1">Inflation Sensitivity</div>
              <div className="text-xl">{result.firm_value?.inflation_sensitivity?.toFixed(2) ?? "N/A"}</div>
            </div>
            <div className="p-3 rounded" style={{ background: "var(--panel-bg-alt)" }}>
              <div className="text-xs text-neutral-500 mb-1">Currency Sensitivity</div>
              <div className="text-xl">{result.firm_value?.currency_sensitivity?.toFixed(2) ?? "N/A"}</div>
            </div>
          </div>
          {result.warnings && result.warnings.length > 0 && (
            <div className="mt-4 p-3 border rounded" style={{ color: "var(--warning)", background: "var(--warning-bg)", borderColor: "var(--warning-border)" }}>
              <div className="text-xs font-semibold uppercase mb-2">Warnings</div>
              <ul className="list-disc list-inside text-sm space-y-1">
                {result.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
