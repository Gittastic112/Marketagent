"use client";

import { useId, useState } from "react";
import type { AllocationRequest, PeerDiscoveryRequest, ReportObservation, ReportRequest, ResearchDataset, ResearchKind, ResearchRequestByKind, SimulationRequest } from "@/lib/api/research-lab";
import { parseResearchJson, researchNumber } from "@/lib/research-lab-input";
import { ResearchJsonInput } from "./json-input";

export const RESEARCH_KIND_LABELS: Record<ResearchKind, string> = {
  allocation: "Portfolio allocation", simulation: "Rebalancing simulation", report: "Return report", peers: "Peer discovery",
};

export function ResearchRunForm({ kind, busy, onSubmit }: {
  kind: ResearchKind; busy: boolean;
  onSubmit: <K extends ResearchKind>(kind: K, payload: ResearchRequestByKind[K]) => Promise<void>;
}) {
  const id = useId();
  const [dataset, setDataset] = useState("");
  const [objective, setObjective] = useState<AllocationRequest["objective"]>("equal_weight");
  const [covariance, setCovariance] = useState<AllocationRequest["covariance"]>("ledoit_wolf");
  const [minimum, setMinimum] = useState("0");
  const [maximum, setMaximum] = useState("1");
  const [riskFree, setRiskFree] = useState("0.04");
  const [expected, setExpected] = useState("");
  const [groups, setGroups] = useState("");
  const [baseline, setBaseline] = useState("");
  const [turnover, setTurnover] = useState("");
  const [weights, setWeights] = useState("");
  const [strategy, setStrategy] = useState<SimulationRequest["strategy"]>("buy_and_hold");
  const [rebalance, setRebalance] = useState<SimulationRequest["rebalance"]>("monthly");
  const [decisionDate, setDecisionDate] = useState("");
  const [costs, setCosts] = useState("0");
  const [engine, setEngine] = useState<SimulationRequest["engine"]>("native");
  const [reportReturns, setReportReturns] = useState("");
  const [benchmark, setBenchmark] = useState("");
  const [title, setTitle] = useState("Research return report");
  const [source, setSource] = useState("");
  const [periods, setPeriods] = useState("252");
  const [country, setCountry] = useState("");
  const [sector, setSector] = useState("");
  const [industry, setIndustry] = useState("");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState("50");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    setError("");
    try {
      if (kind === "allocation") {
        const payload: AllocationRequest = {
          dataset: parseResearchJson<ResearchDataset>(dataset, "Return dataset", "object"), objective, covariance,
          min_weight: researchNumber(minimum, "Minimum weight"), max_weight: researchNumber(maximum, "Maximum weight"),
          risk_free_rate: researchNumber(riskFree, "Risk-free rate"),
        };
        if (expected.trim()) payload.annual_expected_returns = parseResearchJson(expected, "Annual expected returns", "object");
        if (groups.trim()) payload.groups = parseResearchJson(groups, "Group constraints", "array");
        if (baseline.trim()) payload.baseline_weights = parseResearchJson(baseline, "Baseline weights", "object");
        if (turnover.trim()) payload.max_turnover = researchNumber(turnover, "Maximum gross turnover");
        await onSubmit(kind, payload);
      } else if (kind === "simulation") {
        const payload: SimulationRequest = {
          dataset: parseResearchJson<ResearchDataset>(dataset, "Return dataset", "object"),
          initial_weights: parseResearchJson(weights, "Initial weights", "object"), strategy, rebalance, engine,
          weight_decision_date: decisionDate, transaction_cost_bps: researchNumber(costs, "Transaction costs"),
        };
        await onSubmit(kind, payload);
      } else if (kind === "report") {
        const payload: ReportRequest = {
          returns: parseResearchJson<ReportObservation[]>(reportReturns, "Report returns", "array"),
          title, source_label: source, periods_per_year: researchNumber(periods, "Periods per year"), risk_free_rate: researchNumber(riskFree, "Risk-free rate"),
        };
        if (benchmark.trim()) payload.benchmark = parseResearchJson(benchmark, "Benchmark returns", "array");
        await onSubmit(kind, payload);
      } else {
        const payload: PeerDiscoveryRequest = { limit: researchNumber(limit, "Result limit") };
        if (country.trim()) payload.country = country.trim();
        if (sector.trim()) payload.sector = sector.trim();
        if (industry.trim()) payload.industry = industry.trim();
        if (query.trim()) payload.query = query.trim();
        await onSubmit(kind, payload);
      }
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Research inputs could not be submitted."); }
  }

  return <form onSubmit={submit} aria-label={`${RESEARCH_KIND_LABELS[kind]} inputs`}>
    <fieldset disabled={busy} className="research-lab-fieldset">
      <legend>{RESEARCH_KIND_LABELS[kind]} inputs</legend>
      {(kind === "allocation" || kind === "simulation") && <>
        <ResearchJsonInput label="Return dataset JSON" value={dataset} onChange={setDataset}
          description="Dated, aligned decimal returns in one base currency. Include source_label, return_basis, periods_per_year, assets and observations. No prices or returns are downloaded automatically. Server validation remains authoritative." />
        <details><summary>Dataset format and requirements</summary>
          <p>Every interval must contain every asset. Intervals must be contiguous and ordered. Allocation requires at least two assets and max(20, asset count + 1) intervals. Limits: 40 assets and 2,600 intervals. No implicit FX conversion or missing-return filling.</p>
          <p><strong>Mock Data shape example only.</strong> The two intervals below illustrate the format and are insufficient for allocation. This example is never loaded into the form.</p>
          <pre>{JSON.stringify({ base_currency: "USD", periods_per_year: 252, return_basis: "total_return", source_label: "Mock Data format example",
            assets: [{ key: "EXAMPLE_US", ticker: "EXAMPLE", currency: "USD" }], observations: [
              { start_date: "2025-01-02", end_date: "2025-01-03", returns: { EXAMPLE_US: 0.01 } },
              { start_date: "2025-01-03", end_date: "2025-01-06", returns: { EXAMPLE_US: -0.02 } },
            ] }, null, 2)}</pre>
        </details>
      </>}
      {kind === "allocation" && <>
        <div className="form-grid">
          <div className="field"><label htmlFor={`${id}-objective`}>Objective</label><select id={`${id}-objective`} value={objective} onChange={event => setObjective(event.target.value as AllocationRequest["objective"])}>
            <option value="equal_weight">Equal weight (native)</option><option value="min_volatility">Minimum volatility</option><option value="max_sharpe">Maximum Sharpe with explicit forecasts</option><option value="hrp">Hierarchical risk parity</option>
          </select></div>
          <div className="field"><label htmlFor={`${id}-covariance`}>Covariance method</label><select id={`${id}-covariance`} value={covariance} onChange={event => setCovariance(event.target.value as AllocationRequest["covariance"])}>
            <option value="ledoit_wolf">Ledoit-Wolf</option><option value="sample">Sample covariance</option></select></div>
          <div className="field"><label htmlFor={`${id}-min`}>Minimum asset weight (decimal)</label><input id={`${id}-min`} type="number" min={0} max={1} step="any" required value={minimum} onChange={event => setMinimum(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-max`}>Maximum asset weight (decimal)</label><input id={`${id}-max`} type="number" min={0} max={1} step="any" required value={maximum} onChange={event => setMaximum(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-rf`}>Annual risk-free rate (decimal)</label><input id={`${id}-rf`} type="number" min={-0.999999} max={1} step="any" required value={riskFree} onChange={event => setRiskFree(event.target.value)} /></div>
        </div>
        <p className="basis-note">Weights are hypothetical Calculations, not trading instructions. Valuation upside is not an annual return forecast. HRP supports default asset bounds only; the server rejects unsupported constraint combinations.</p>
        <ResearchJsonInput label="Annual expected returns JSON" value={expected} onChange={setExpected} rows={3} required={objective === "max_sharpe"}
          description="Optional explicit annual decimal forecasts keyed by every asset. Required for maximum Sharpe. These remain user assumptions." />
        <details><summary>Group and turnover constraints</summary>
          <ResearchJsonInput label="Group constraints JSON" value={groups} onChange={setGroups} rows={4} required={false} description="Array of objects with name, members (asset keys), min_weight and max_weight. Unsupported HRP constraints are rejected." />
          <ResearchJsonInput label="Baseline weights JSON" value={baseline} onChange={setBaseline} rows={3} required={false} description="Object keyed by all assets, with decimal weights summing to one. Required when bounding turnover." />
          <div className="field"><label htmlFor={`${id}-turnover`}>Maximum gross turnover (optional, 0 to 2)</label><input id={`${id}-turnover`} type="number" min={0} max={2} step="any" value={turnover} onChange={event => setTurnover(event.target.value)} /></div>
        </details>
      </>}
      {kind === "simulation" && <>
        <ResearchJsonInput label="Initial weights JSON" value={weights} onChange={setWeights} rows={3} description="Object keyed by every asset. Decimal weights must sum to one; the backend validates them." />
        <div className="form-grid">
          <div className="field"><label htmlFor={`${id}-strategy`}>Strategy</label><select id={`${id}-strategy`} value={strategy} onChange={event => setStrategy(event.target.value as SimulationRequest["strategy"])}><option value="buy_and_hold">Buy and hold</option><option value="constant_weight">Constant weight</option></select></div>
          <div className="field"><label htmlFor={`${id}-rebalance`}>Rebalance interval</label><select id={`${id}-rebalance`} value={rebalance} disabled={strategy === "buy_and_hold"} onChange={event => setRebalance(event.target.value as SimulationRequest["rebalance"])}>
            <option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="yearly">Yearly</option><option value="each_period">Each period</option></select></div>
          <div className="field"><label htmlFor={`${id}-decision`}>Weight decision date</label><input id={`${id}-decision`} type="date" value={decisionDate} required onChange={event => setDecisionDate(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-costs`}>Transaction costs (basis points)</label><input id={`${id}-costs`} type="number" min={0} max={1000} step="any" value={costs} required onChange={event => setCosts(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-engine`}>Engine</label><select id={`${id}-engine`} value={engine} onChange={event => setEngine(event.target.value as SimulationRequest["engine"])}><option value="native">Native explicit simulation</option><option value="bt">bt zero-cost cross-check</option></select></div>
        </div>
        <p className="basis-note">The decision date must precede or equal the first return interval. Historical availability and universe selection are not independently verified. The bt cross-check accepts zero costs only. Actual holdings remain unchanged.</p>
      </>}
      {kind === "report" && <>
        <div className="form-grid">
          <div className="field"><label htmlFor={`${id}-title`}>Report title</label><input id={`${id}-title`} value={title} required maxLength={120} onChange={event => setTitle(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-source`}>Input source description</label><input id={`${id}-source`} value={source} required minLength={3} maxLength={300} onChange={event => setSource(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-periods`}>Periods per year</label><input id={`${id}-periods`} type="number" min={1} max={366} step={1} value={periods} required onChange={event => setPeriods(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-report-rf`}>Annual risk-free rate (decimal)</label><input id={`${id}-report-rf`} type="number" min={-0.999999} max={1} step="any" value={riskFree} required onChange={event => setRiskFree(event.target.value)} /></div>
        </div>
        <ResearchJsonInput label="Report returns JSON" value={reportReturns} onChange={setReportReturns} description='Array of {"date":"YYYY-MM-DD","return_decimal":0.01}. Dates must be increasing and unique; returns are decimals, not percentages.' />
        <ResearchJsonInput label="Benchmark returns JSON" value={benchmark} onChange={setBenchmark} rows={5} required={false} description="Optional array in the same format, on exactly the same dates. No automatic alignment or missing-value filling." />
      </>}
      {kind === "peers" && <>
        <p>Search the configured, pinned FinanceDatabase reference snapshot. Results are discovery candidates, not reviewed comparable-company multiples or current market facts.</p>
        <div className="form-grid">
          <div className="field"><label htmlFor={`${id}-country`}>Country (optional)</label><input id={`${id}-country`} value={country} maxLength={100} onChange={event => setCountry(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-sector`}>Sector (optional)</label><input id={`${id}-sector`} value={sector} maxLength={100} onChange={event => setSector(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-industry`}>Industry (optional)</label><input id={`${id}-industry`} value={industry} maxLength={120} onChange={event => setIndustry(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-query`}>Name or symbol (optional)</label><input id={`${id}-query`} value={query} minLength={2} maxLength={100} onChange={event => setQuery(event.target.value)} /></div>
          <div className="field"><label htmlFor={`${id}-limit`}>Result limit</label><input id={`${id}-limit`} type="number" min={1} max={100} value={limit} required onChange={event => setLimit(event.target.value)} /></div>
        </div>
      </>}
      {error && <p role="alert">{error}</p>}
      <div className="button-row"><button type="submit">{busy ? "Running research…" : `Run ${RESEARCH_KIND_LABELS[kind].toLowerCase()}`}</button></div>
    </fieldset>
  </form>;
}
