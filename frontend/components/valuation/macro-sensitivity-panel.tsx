"use client";

import { useState } from "react";
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
    setLoading(true);
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
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to run calculation");
    } finally {
      setLoading(false);
    }
  };

  const handleRunTopDown = async () => {
    setLoading(true);
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
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to run regression");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-neutral-800 bg-neutral-900 rounded-lg p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-neutral-100">Macro Sensitivity Engine</h3>
        <div className="flex bg-neutral-800 rounded p-1">
          <button
            onClick={() => setMode("bottom_up")}
            className={`px-3 py-1 text-sm rounded ${
              mode === "bottom_up" ? "bg-neutral-700 text-white" : "text-neutral-400 hover:text-white"
            }`}
          >
            Bottom-Up (Segments)
          </button>
          <button
            onClick={() => setMode("top_down")}
            className={`px-3 py-1 text-sm rounded ${
              mode === "top_down" ? "bg-neutral-700 text-white" : "text-neutral-400 hover:text-white"
            }`}
          >
            Top-Down (Regression)
          </button>
        </div>
      </div>

      {mode === "bottom_up" ? (
        <div className="space-y-4">
          <div className="border border-neutral-800 rounded bg-neutral-950 p-2 space-y-2">
            <div className="grid grid-cols-4 gap-2 text-xs text-neutral-500 font-semibold px-2">
              <div className="col-span-2">Segment Name</div>
              <div>SIC Code</div>
              <div>Weight (0-1)</div>
            </div>
            {segments.map((seg, idx) => (
              <div key={idx} className="grid grid-cols-4 gap-2 px-2">
                <input
                  type="text"
                  value={seg.segment_name}
                  onChange={(e) => {
                    const newSegs = [...segments];
                    newSegs[idx].segment_name = e.target.value;
                    setSegments(newSegs);
                  }}
                  className="col-span-2 bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-sm text-neutral-200"
                />
                <input
                  type="text"
                  value={seg.sic_code || ""}
                  onChange={(e) => {
                    const newSegs = [...segments];
                    newSegs[idx].sic_code = e.target.value;
                    setSegments(newSegs);
                  }}
                  className="bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-sm text-neutral-200"
                  placeholder="e.g. 7372"
                />
                <input
                  type="number"
                  step="0.1"
                  value={seg.segment_weight ?? ""}
                  onChange={(e) => {
                    const newSegs = [...segments];
                    newSegs[idx].segment_weight = e.target.value === "" ? null : Number(e.target.value);
                    setSegments(newSegs);
                  }}
                  className="bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-sm text-neutral-200"
                />
              </div>
            ))}
          </div>
          <button
            onClick={handleRunBottomUp}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            {loading ? "Calculating..." : "Run Bottom-Up Calculation"}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="border border-neutral-800 rounded bg-neutral-950 p-2 space-y-2">
            <div className="grid grid-cols-4 gap-2 text-xs text-neutral-500 font-semibold px-2">
              <div>Period</div>
              <div>Operating Income</div>
              <div>Market Cap</div>
              <div>Total Debt</div>
            </div>
            {periods.map((p, idx) => (
              <div key={idx} className="space-y-2 px-2">
                <div className="grid grid-cols-4 gap-2">
                  <input
                    aria-label={`Period ${idx + 1}`}
                    type="text"
                    value={p.period_label}
                    onChange={(e) => {
                      const newPeriods = [...periods];
                      newPeriods[idx].period_label = e.target.value;
                      setPeriods(newPeriods);
                    }}
                    className="bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-sm text-neutral-200"
                  />
                  {(["operating_income", "market_cap", "total_debt"] as const).map((field) => (
                    <input
                      aria-label={`${field.replaceAll("_", " ")} ${idx + 1}`}
                      className="bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-sm text-neutral-200"
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
                </div>
                <div className="grid grid-cols-4 gap-2">
                  {([
                    ["change_in_long_term_bond_rate", "Rate change"],
                    ["gdp_growth", "GDP growth"],
                    ["inflation_change", "Inflation change"],
                    ["currency_change", "Currency change"],
                  ] as const).map(([field, placeholder]) => (
                    <input
                      aria-label={`${placeholder} ${idx + 1}`}
                      className="bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-sm text-neutral-200"
                      key={field}
                      onChange={(e) => {
                        const newPeriods = [...periods];
                        newPeriods[idx][field] = e.target.value === "" ? null : Number(e.target.value);
                        setPeriods(newPeriods);
                      }}
                      placeholder={placeholder}
                      step="0.0001"
                      type="number"
                      value={p[field] ?? ""}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={handleRunTopDown}
            disabled={loading}
            className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            {loading ? "Running Regression..." : "Run Top-Down Regression"}
          </button>
        </div>
      )}

      {error && <div className="text-red-400 text-sm mt-4 p-2 bg-red-900/20 border border-red-900/50 rounded">{error}</div>}

      {result && (
        <div className="mt-6 border-t border-neutral-800 pt-4">
          <h4 className="text-md font-semibold text-neutral-200 mb-4">Results ({result.method})</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-neutral-800/50 p-3 rounded">
              <div className="text-xs text-neutral-500 mb-1">Duration</div>
              <div className="text-xl text-neutral-100">{result.firm_value?.duration?.toFixed(2) ?? "N/A"}</div>
            </div>
            <div className="bg-neutral-800/50 p-3 rounded">
              <div className="text-xs text-neutral-500 mb-1">Cyclicality</div>
              <div className="text-xl text-neutral-100">{result.firm_value?.cyclicality?.toFixed(2) ?? "N/A"}</div>
            </div>
            <div className="bg-neutral-800/50 p-3 rounded">
              <div className="text-xs text-neutral-500 mb-1">Inflation Sensitivity</div>
              <div className="text-xl text-neutral-100">{result.firm_value?.inflation_sensitivity?.toFixed(2) ?? "N/A"}</div>
            </div>
            <div className="bg-neutral-800/50 p-3 rounded">
              <div className="text-xs text-neutral-500 mb-1">Currency Sensitivity</div>
              <div className="text-xl text-neutral-100">{result.firm_value?.currency_sensitivity?.toFixed(2) ?? "N/A"}</div>
            </div>
          </div>
          {result.warnings && result.warnings.length > 0 && (
            <div className="mt-4 p-3 bg-amber-900/20 border border-amber-900/50 rounded">
              <div className="text-amber-500 text-xs font-semibold uppercase mb-2">Warnings</div>
              <ul className="list-disc list-inside text-sm text-amber-200/80 space-y-1">
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
