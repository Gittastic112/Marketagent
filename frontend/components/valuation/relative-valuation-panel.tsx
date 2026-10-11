"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import {
  getRelativeValuationCountries,
  getRelativeValuationIndustries,
  listPeerValuationSets,
  PeerSetMethodSource,
  PeerValuationSet,
  PricingSourceProvenance,
  runRelativeValuation,
  RelativeValuationResponse,
  RelativeValuationRequest
} from "@/lib/api";
import { PeerSetManager } from "@/components/valuation/peer-set-manager";
import { RelativeInputBasis } from "./relative-input-basis";
import { createRequestGate } from "@/lib/latest-request";
import { useLatestResource } from "@/lib/use-latest-resource";
import { hasReadySelection, isPeerSetCalculationReady } from "@/lib/relative-valuation-selection";

type PanelProps = {
  companyId?: string;
  financials: RelativeValuationRequest["financials"];
  runValuation?: typeof runRelativeValuation;
  inputContextKey?: string;
  inputBlockedReason?: string;
};

function RequestNotice({ label, resource }: {
  label: string;
  resource: { status: string; error: string | null; reload: () => Promise<void> };
}) {
  if (resource.status === "loading") return <p role="status">Loading {label}...</p>;
  if (resource.status !== "error") return null;
  return <div role="alert" style={{ marginBottom: "12px", color: "#b71c1c" }}>
    <p>{label} unavailable: {resource.error}</p>
    <button type="button" onClick={() => { void resource.reload().catch(() => {}); }}>Retry {label}</button>
  </div>;
}

export function RelativeValuationPanel(props: PanelProps) {
  // Never carry an old company's peer editor, requests, or results into another company.
  return <CompanyRelativeValuationPanel key={props.companyId || "unassigned"} {...props} />;
}

function CompanyRelativeValuationPanel({
  companyId,
  financials,
  runValuation = runRelativeValuation,
  inputContextKey,
  inputBlockedReason,
}: PanelProps) {
  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [selectedIndustry, setSelectedIndustry] = useState<string>("");
  const [benchmarkMode, setBenchmarkMode] = useState<"industry_aggregate" | "reviewed_peer_set">("industry_aggregate");
  const [selectedPeerSetId, setSelectedPeerSetId] = useState<string>("");
  const [methods, setMethods] = useState<string[]>(["pe", "pbv", "ps", "ev_sales", "ev_ebitda", "ev_ebit"]);
  const countryResource = useLatestResource(getRelativeValuationCountries);
  const industryLoader = useCallback(() => selectedCountry
    ? getRelativeValuationIndustries(selectedCountry) : Promise.resolve<string[]>([]), [selectedCountry]);
  const industryResource = useLatestResource(industryLoader);
  const peerLoader = useCallback(() => companyId
    ? listPeerValuationSets(Number(companyId), true) : Promise.resolve<PeerValuationSet[]>([]), [companyId]);
  const peerResource = useLatestResource(peerLoader);
  const countries = countryResource.data || [];
  const industries = industryResource.data || [];
  const peerSets = peerResource.data || [];
  const eligiblePeerIds = peerSets.filter(isPeerSetCalculationReady).map(set => String(set.id));
  const benchmarkReady = benchmarkMode === "industry_aggregate"
    ? hasReadySelection(countryResource.status, countries, selectedCountry)
      && hasReadySelection(industryResource.status, industries, selectedIndustry)
    : Boolean(companyId) && hasReadySelection(peerResource.status, eligiblePeerIds, selectedPeerSetId);

  const [result, setResult] = useState<RelativeValuationResponse | null>(null);
  const [resultInputKey, setResultInputKey] = useState<string | null>(null);
  const currentInputKey = JSON.stringify({ companyId, financials, inputContextKey, inputBlockedReason, benchmarkMode, selectedCountry,
    selectedIndustry, selectedPeerSetId, methods,
    peerEvidence: peerSets.find(set => String(set.id) === selectedPeerSetId),
    evidenceRevision: benchmarkMode === "industry_aggregate"
      ? [countryResource.revision, industryResource.revision] : peerResource.revision,
    benchmarkReady,
  });
  const inputKeyRef = useRef(currentInputKey);
  inputKeyRef.current = currentInputKey;
  const runGate = useMemo(createRequestGate, []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (countryResource.status !== "ready") return;
    setSelectedCountry(current => countryResource.data?.includes(current)
      ? current : countryResource.data?.[0] || "");
  }, [countryResource.status, countryResource.data]);

  const refreshPeerSets = useCallback(async () => {
    runGate.invalidate();
    setResult(null);
    await peerResource.reload();
  }, [peerResource.reload, runGate]);

  useEffect(() => {
    if (peerResource.status !== "ready") return;
    const reviewed = (peerResource.data || []).filter(isPeerSetCalculationReady);
    setSelectedPeerSetId(current => reviewed.some(set => String(set.id) === current)
      ? current : String(reviewed[0]?.id || ""));
  }, [peerResource.status, peerResource.data]);

  useEffect(() => {
    runGate.invalidate();
    setLoading(false);
    setResult(null);
    setError(null);
    return runGate.invalidate;
  }, [currentInputKey, runGate]);

  const handleRun = async () => {
    if (inputBlockedReason) {
      setError(inputBlockedReason);
      return;
    }
    if (methods.length === 0) {
      setError("Select at least one multiple");
      return;
    }
    if (!benchmarkReady) {
      setError("Load current benchmark evidence and select an eligible benchmark");
      return;
    }

    const isLatestRun = runGate.begin();
    const canPublish = () => isLatestRun() && inputKeyRef.current === currentInputKey;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await runValuation({
        companyId,
        country: benchmarkMode === "industry_aggregate" ? selectedCountry : undefined,
        industryName: benchmarkMode === "industry_aggregate" ? selectedIndustry : undefined,
        peerSetId: benchmarkMode === "reviewed_peer_set" ? Number(selectedPeerSetId) : undefined,
        financials,
        methods
      });
      if (canPublish()) {
        setResultInputKey(currentInputKey);
        setResult(res);
      }
    } catch (err: unknown) {
      if (canPublish()) setError(err instanceof Error ? err.message : "Failed to run relative valuation");
    } finally {
      if (canPublish()) setLoading(false);
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

      <div style={{ marginBottom: "1rem" }}>
        <label style={{ display: "block", marginBottom: "4px", fontSize: "0.875rem", fontWeight: 500 }} htmlFor="relative-valuation-benchmark-mode">Benchmark basis</label>
        <select
          id="relative-valuation-benchmark-mode"
          value={benchmarkMode}
          onChange={(event) => {
            setBenchmarkMode(event.target.value as "industry_aggregate" | "reviewed_peer_set");
            setResult(null);
            setError(null);
          }}
          style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
        >
          <option value="industry_aggregate">Source-backed industry aggregate</option>
          <option value="reviewed_peer_set">User-reviewed peer set</option>
        </select>
      </div>

      {benchmarkMode === "industry_aggregate" ? <div style={{ display: "flex", gap: "16px", marginBottom: "16px", flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: "200px" }}>
          <label htmlFor="relative-valuation-country" style={{ display: "block", marginBottom: "4px", fontSize: "0.875rem", fontWeight: 500 }}>Region / Country</label>
          <select
            id="relative-valuation-country"
            value={selectedCountry}
            onChange={(e) => { setSelectedCountry(e.target.value); setSelectedIndustry(""); }}
            disabled={countryResource.status !== "ready" || countries.length === 0}
            style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
          >
            {countries.length === 0 && <option value="">{countryResource.status === "ready" ? "No active pricing sources" : "Countries unavailable"}</option>}
            {countries.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <RequestNotice label="benchmark countries" resource={countryResource} />
        </div>

        <div style={{ flex: 1, minWidth: "200px" }}>
          <label htmlFor="relative-valuation-industry" style={{ display: "block", marginBottom: "4px", fontSize: "0.875rem", fontWeight: 500 }}>Industry</label>
          <select
            id="relative-valuation-industry"
            value={selectedIndustry}
            onChange={(e) => setSelectedIndustry(e.target.value)}
            disabled={!selectedCountry || industryResource.status !== "ready" || industries.length === 0}
            style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
          >
            <option value="">Select an industry...</option>
            {industries.map(i => <option key={i} value={i}>{i}</option>)}
          </select>
          {selectedCountry && <RequestNotice label="benchmark industries" resource={industryResource} />}
          {selectedCountry && industryResource.status === "ready" && industries.length === 0 && (
            <p>No active industry benchmarks for this country. Choose another country or import supported pricing sources.</p>
          )}
        </div>
      </div> : (
        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor="relative-valuation-peer-set" style={{ display: "block", marginBottom: "4px", fontSize: "0.875rem", fontWeight: 500 }}>Reviewed peer set</label>
          <select
            id="relative-valuation-peer-set"
            value={selectedPeerSetId}
            onChange={(event) => { setSelectedPeerSetId(event.target.value); setResult(null); }}
            disabled={!companyId || peerResource.status !== "ready" || eligiblePeerIds.length === 0}
            style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
          >
            <option value="">Select a reviewed peer set...</option>
            {peerSets.filter(isPeerSetCalculationReady).map((peerSet) => (
              <option key={peerSet.id} value={peerSet.id}>{peerSet.name} · {peerSet.includedMemberCount} peers</option>
            ))}
          </select>
          {!companyId ? <p>Select a company before using reviewed peer evidence.</p> : <>
            <RequestNotice label="peer evidence" resource={{ ...peerResource, reload: refreshPeerSets }} />
            {peerResource.status === "ready" && <button type="button" onClick={() => { void refreshPeerSets().catch(() => {}); }}>Refresh peer evidence</button>}
          </>}
          {companyId && peerResource.status === "ready" && eligiblePeerIds.length === 0 && (
            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
              No eligible reviewed peer set is available. Check evidence conflicts, method coverage, and the current diagnostic receipt below.
            </p>
          )}
        </div>
      )}

      {companyId && (
        <PeerSetManager
          companyId={Number(companyId)}
          peerSets={peerSets}
          onChanged={refreshPeerSets}
        />
      )}

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
          type="button"
          onClick={handleRun}
          disabled={loading || !benchmarkReady || methods.length === 0 || Boolean(inputBlockedReason)}
          style={{
            backgroundColor: "#000", color: "#fff", border: "none",
            padding: "8px 16px", borderRadius: "4px", cursor: loading || !benchmarkReady || methods.length === 0 ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Calculating..." : "Run Valuation"}
        </button>
      </div>

      {inputBlockedReason && <p role="status">{inputBlockedReason}</p>}

      {error && (
        <div role="alert" style={{ color: "#d32f2f", backgroundColor: "#ffebee", padding: "12px", borderRadius: "4px", marginBottom: "16px", fontSize: "0.875rem" }}>
          {error}
        </div>
      )}

      {result && !inputBlockedReason && benchmarkReady && resultInputKey === currentInputKey && (
        <div style={{ borderTop: "1px solid #eaeaea", paddingTop: "16px" }}>
          {result.inputBasis && <RelativeInputBasis basis={result.inputBasis} />}
          <h4 style={{ margin: "0 0 12px 0" }}>
            Results against {result.benchmarkType === "reviewed_peer_set" ? result.peerSet?.name : result.industryName}
          </h4>
          <p style={{ margin: "0 0 12px 0", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
            {result.benchmarkType === "reviewed_peer_set"
              ? `Calculation using the reviewed median for ${result.peerSet?.includedMemberCount || 0} included peers.`
              : "Calculation using active source-backed industry pricing aggregates."}
          </p>

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

          <div className="relative-table-scroll" tabIndex={0} role="region" aria-label="Relative valuation method results">
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
          </div>

          <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid #eaeaea", fontSize: "0.75rem", color: "#555" }}>
            {result.benchmarkSources.map((source: PricingSourceProvenance) => (
              <div key={source.datasetVersionId} style={{ marginBottom: "4px" }}>
                <strong>{source.sourceCode.toUpperCase()}</strong>: {source.sourceFile}, version {source.datasetVersionId}, as of {source.sourceAsOf || "unknown"}, {source.dateConfidence} date confidence
              </div>
            ))}
            {result.relativeValues.flatMap((value) => (
              "peerSetId" in value.source ? [value.source as PeerSetMethodSource] : []
            )).filter((source, index, sources) => sources.findIndex((candidate) => candidate.peerSetId === source.peerSetId && candidate.formula === source.formula) === index).map((source) => (
              <div key={`${source.peerSetId}-${source.formula}`} style={{ marginBottom: "6px" }}>
                <strong>{source.peerSetName}</strong>: {source.formula}; {source.eligibleCount} reviewed peer sources.
                {source.memberSources.map((member) => (
                  <div key={member.identifier}>
                    {member.identifier}: <a href={member.sourceUrl} target="_blank" rel="noreferrer">{member.sourceName}</a>, as of {member.sourceAsOf}, {member.claimType}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
