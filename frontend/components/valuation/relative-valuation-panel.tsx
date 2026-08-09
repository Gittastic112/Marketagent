"use client";

import { useState, useEffect } from "react";
import {
  getRelativeValuationCountries,
  getRelativeValuationIndustries,
  runRelativeValuation,
  RelativeValuationResponse,
  RelativeValuationRequest
} from "@/lib/api";

export function RelativeValuationPanel({
  companyId,
  financials
}: {
  companyId?: string,
  financials: RelativeValuationRequest["financials"]
}) {
  const [countries, setCountries] = useState<string[]>([]);
  const [industries, setIndustries] = useState<string[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [selectedIndustry, setSelectedIndustry] = useState<string>("");
  const [methods, setMethods] = useState<string[]>(["pe", "pbv", "ps", "ev_sales", "ev_ebitda", "ev_ebit"]);

  const [result, setResult] = useState<RelativeValuationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRelativeValuationCountries()
      .then((availableCountries) => {
        setCountries(availableCountries);
        setSelectedCountry((current) => current || availableCountries[0] || "");
      })
      .catch((err: Error) => setError(err.message || "Failed to load benchmark countries"));
  }, []);

  useEffect(() => {
    if (selectedCountry) {
      setSelectedIndustry("");
      setResult(null);
      setError(null);
      getRelativeValuationIndustries(selectedCountry)
        .then(setIndustries)
        .catch((err: Error) => setError(err.message || "Failed to load benchmark industries"));
    }
  }, [selectedCountry]);

  const handleRun = async () => {
    if (!selectedIndustry) {
      setError("Please select an industry");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await runRelativeValuation({
        companyId,
        country: selectedCountry,
        industryName: selectedIndustry,
        financials,
        methods
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to run relative valuation");
    } finally {
      setLoading(false);
    }
  };

  const toggleMethod = (method: string) => {
    setMethods(prev =>
      prev.includes(method) ? prev.filter(m => m !== method) : [...prev, method]
    );
  };

  return (
    <div className="valuation-panel" style={{ border: "1px solid #eaeaea", borderRadius: "8px", padding: "16px", marginTop: "16px", backgroundColor: "#fafafa" }}>
      <h3 style={{ marginTop: 0, marginBottom: "16px" }}>Relative Valuation</h3>

      <div style={{ display: "flex", gap: "16px", marginBottom: "16px", flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: "200px" }}>
          <label style={{ display: "block", marginBottom: "4px", fontSize: "0.875rem", fontWeight: 500 }}>Region / Country</label>
          <select
            value={selectedCountry}
            onChange={(e) => setSelectedCountry(e.target.value)}
            disabled={countries.length === 0}
            style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
          >
            {countries.length === 0 && <option value="">No active pricing sources</option>}
            {countries.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div style={{ flex: 1, minWidth: "200px" }}>
          <label style={{ display: "block", marginBottom: "4px", fontSize: "0.875rem", fontWeight: 500 }}>Industry</label>
          <select
            value={selectedIndustry}
            onChange={(e) => setSelectedIndustry(e.target.value)}
            style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
          >
            <option value="">Select an industry...</option>
            {industries.map(i => <option key={i} value={i}>{i}</option>)}
          </select>
        </div>
      </div>

      <div style={{ marginBottom: "16px" }}>
        <label style={{ display: "block", marginBottom: "4px", fontSize: "0.875rem", fontWeight: 500 }}>Multiples to apply</label>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", fontSize: "0.875rem" }}>
          {[
            { id: "pe", label: "P/E" },
            { id: "pbv", label: "P/B" },
            { id: "ps", label: "P/S" },
            { id: "ev_sales", label: "EV/Sales" },
            { id: "ev_ebitda", label: "EV/EBITDA" },
            { id: "ev_ebit", label: "EV/EBIT" }
          ].map(m => (
            <label key={m.id} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <input
                type="checkbox"
                checked={methods.includes(m.id)}
                onChange={() => toggleMethod(m.id)}
              />
              {m.label}
            </label>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: "16px" }}>
        <button
          onClick={handleRun}
          disabled={loading || !selectedIndustry}
          style={{
            backgroundColor: "#000", color: "#fff", border: "none",
            padding: "8px 16px", borderRadius: "4px", cursor: loading || !selectedIndustry ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Calculating..." : "Run Valuation"}
        </button>
      </div>

      {error && (
        <div style={{ color: "#d32f2f", backgroundColor: "#ffebee", padding: "12px", borderRadius: "4px", marginBottom: "16px", fontSize: "0.875rem" }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ borderTop: "1px solid #eaeaea", paddingTop: "16px" }}>
          <h4 style={{ margin: "0 0 12px 0" }}>Results against {result.industryName}</h4>

          {result.diagnostics.length > 0 && (
            <div style={{ backgroundColor: "#fff3cd", color: "#856404", padding: "12px", borderRadius: "4px", marginBottom: "16px", fontSize: "0.875rem" }}>
              <strong>Note:</strong>
              <ul style={{ margin: "4px 0 0 0", paddingLeft: "20px" }}>
                {result.diagnostics.map((d, i) => <li key={i}>{d}</li>)}
              </ul>
            </div>
          )}

          {result.unavailableMethods.length > 0 && (
            <div style={{ backgroundColor: "#fff8e1", color: "#6d4c00", padding: "12px", borderRadius: "4px", marginBottom: "16px", fontSize: "0.875rem" }}>
              <strong>Unavailable methods</strong>
              <ul style={{ margin: "4px 0 0 0", paddingLeft: "20px" }}>
                {result.unavailableMethods.map((item) => (
                  <li key={item.method}>{item.method.toUpperCase()}: {item.reason}</li>
                ))}
              </ul>
            </div>
          )}

          {result.range && (
            <div style={{ backgroundColor: "#e3f2fd", color: "#0d47a1", padding: "12px", borderRadius: "4px", marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div><strong>Implied Range:</strong></div>
              <div>
                <span style={{ margin: "0 8px", color: "#555" }}>Low: {result.range.low.toFixed(2)}</span>
                <span style={{ margin: "0 8px", fontWeight: "bold" }}>Avg: {result.range.base.toFixed(2)}</span>
                <span style={{ margin: "0 8px", color: "#555" }}>High: {result.range.high.toFixed(2)}</span>
              </div>
            </div>
          )}

          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #ddd" }}>
                <th style={{ padding: "8px 4px" }}>Method</th>
                <th style={{ padding: "8px 4px" }}>Multiple</th>
                <th style={{ padding: "8px 4px" }}>Implied EV</th>
                <th style={{ padding: "8px 4px" }}>Implied Eq. Value</th>
                <th style={{ padding: "8px 4px" }}>Value / Share</th>
                <th style={{ padding: "8px 4px" }}>Reliability</th>
              </tr>
            </thead>
            <tbody>
              {result.relativeValues.length > 0 ? result.relativeValues.map((v, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #eaeaea" }}>
                  <td style={{ padding: "8px 4px", fontWeight: 500 }}>{v.method}</td>
                  <td style={{ padding: "8px 4px" }}>{v.benchmarkMultiple.toFixed(2)}x</td>
                  <td style={{ padding: "8px 4px" }}>{v.enterpriseValue != null ? v.enterpriseValue.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "-"}</td>
                  <td style={{ padding: "8px 4px" }}>{v.equityValue != null ? v.equityValue.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "-"}</td>
                  <td style={{ padding: "8px 4px", fontWeight: "bold" }}>{v.valuePerShare != null ? v.valuePerShare.toFixed(2) : "-"}</td>
                  <td style={{ padding: "8px 4px" }}>
                    <span style={{
                      padding: "2px 6px", borderRadius: "12px", fontSize: "0.75rem",
                      backgroundColor: v.reliability === "high" ? "#e8f5e9" : v.reliability === "medium" ? "#fff8e1" : "#ffebee",
                      color: v.reliability === "high" ? "#2e7d32" : v.reliability === "medium" ? "#f57f17" : "#c62828"
                    }}>
                      {v.reliability.toUpperCase()}
                    </span>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={6} style={{ padding: "16px", textAlign: "center", color: "#666" }}>
                    No results calculated. Ensure financials and benchmark multiples are available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid #eaeaea", fontSize: "0.75rem", color: "#555" }}>
            {result.benchmarkSources.map((source) => (
              <div key={source.datasetVersionId} style={{ marginBottom: "4px" }}>
                <strong>{source.sourceCode.toUpperCase()}</strong>: {source.sourceFile}, version {source.datasetVersionId}, as of {source.sourceAsOf || "unknown"}, {source.dateConfidence} date confidence
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
