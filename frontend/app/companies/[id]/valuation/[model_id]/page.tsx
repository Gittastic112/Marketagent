import { notFound } from "next/navigation";
import Link from "next/link";
import { fetchApi, Company, listValuationModels, getValuationModelAssumptions } from "@/lib/api";
import type { DcfAssumptionSet, DcfOutput } from "@/lib/api";
import { EmptyState, PageHeader, Panel } from "@/components/page";
import { SelectField, TextField } from "@/components/form-fields";

export const dynamic = "force-dynamic";

function fmt(n: number, decimals = 2): string {
  return n.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function fmtLarge(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

function ProjectionTable({ output, aset }: { output: DcfOutput; aset: DcfAssumptionSet }) {
  const json = output.output_json as {
    projected_fcfs?: number[];
    pv_of_fcfs?: number[];
    terminal_value?: number;
    pv_terminal_value?: number;
  } | null;

  if (!json || !json.projected_fcfs) return null;

  const years = json.projected_fcfs.length;
  const assumptions = aset.assumptions_json as { current_fcf?: number; fcf_growth_rate?: number | number[] };
  const currentFcf = assumptions.current_fcf ?? 0;

  return (
    <div className="table-wrap" style={{ marginTop: "1rem" }}>
      <table>
        <thead>
          <tr>
            <th>Year</th>
            <th style={{ textAlign: "right" }}>Projected FCF</th>
            <th style={{ textAlign: "right" }}>Discount Factor</th>
            <th style={{ textAlign: "right" }}>PV of FCF</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ color: "var(--text-secondary)" }}>
            <td>0 (Base)</td>
            <td style={{ textAlign: "right" }}>{fmtLarge(currentFcf)}</td>
            <td style={{ textAlign: "right" }}>—</td>
            <td style={{ textAlign: "right" }}>—</td>
          </tr>
          {json.projected_fcfs.map((fcf, i) => {
            const pv = json.pv_of_fcfs?.[i] ?? 0;
            const discountFactor = (1 + aset.discount_rate) ** (i + 1);
            return (
              <tr key={i}>
                <td>{i + 1}</td>
                <td style={{ textAlign: "right" }}>{fmtLarge(fcf)}</td>
                <td style={{ textAlign: "right" }}>{fmt(discountFactor, 4)}</td>
                <td style={{ textAlign: "right" }}>{fmtLarge(pv)}</td>
              </tr>
            );
          })}
          <tr style={{ borderTop: "2px solid var(--border-color)", fontWeight: 600 }}>
            <td colSpan={3}>Sum of PV of FCFs</td>
            <td style={{ textAlign: "right" }}>{fmtLarge(json.pv_of_fcfs?.reduce((a, b) => a + b, 0) ?? 0)}</td>
          </tr>
          <tr>
            <td colSpan={3}>Terminal Value (Year {years})</td>
            <td style={{ textAlign: "right" }}>{fmtLarge(json.terminal_value ?? 0)}</td>
          </tr>
          <tr>
            <td colSpan={3}>PV of Terminal Value</td>
            <td style={{ textAlign: "right" }}>{fmtLarge(json.pv_terminal_value ?? 0)}</td>
          </tr>
          <tr style={{ fontWeight: 700, borderTop: "2px solid var(--border-color)" }}>
            <td colSpan={3}>Enterprise Value</td>
            <td style={{ textAlign: "right" }}>{fmtLarge(output.enterprise_value)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function ScenarioBadge({ scenario }: { scenario: string }) {
  const colors: Record<string, string> = {
    Base: "var(--accent)",
    Bull: "var(--success)",
    Bear: "var(--error)",
  };
  const color = colors[scenario] ?? "var(--text-secondary)";
  return (
    <span className="badge" style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}40` }}>
      {scenario}
    </span>
  );
}

export default async function ValuationModelDetailPage(props: { params: Promise<{ id: string; model_id: string }> }) {
  const params = await props.params;
  const companyId = parseInt(params.id, 10);
  const modelId = parseInt(params.model_id, 10);

  if (isNaN(companyId) || isNaN(modelId)) {
    notFound();
  }

  let company: Company;
  try {
    company = await fetchApi<Company>(`/companies/${companyId}`);
  } catch {
    notFound();
  }

  const models = await listValuationModels(companyId);
  const model = models.find((m) => m.id === modelId);

  if (!model) {
    notFound();
  }

  const assumptions = await getValuationModelAssumptions(modelId);

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <PageHeader eyebrow={`${company.ticker} Valuation`} title={model.name} status={model.description ?? undefined} />
        <div style={{ marginBottom: "2rem" }}>
          <Link href={`/companies/${company.id}/valuation`} className="secondary-button">&larr; Back to Models</Link>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "350px 1fr", gap: "1.5rem", alignItems: "start" }}>
        {/* Left: Input Form */}
        <Panel title="New Scenario">
          <form
            action={async (data) => {
              "use server";
              const { createDcfAssumptionSet } = await import("@/app/actions");

              const current_fcf = parseFloat(data.get("current_fcf") as string);
              const shares_outstanding = parseFloat(data.get("shares_outstanding") as string);
              const net_debt = parseFloat(data.get("net_debt") as string);
              const fcf_growth_rate = parseFloat(data.get("fcf_growth_rate") as string);

              const assumptions_json = JSON.stringify({
                current_fcf,
                shares_outstanding,
                net_debt,
                fcf_growth_rate,
              });

              data.set("assumptions_json", assumptions_json);

              await createDcfAssumptionSet(data, modelId.toString(), companyId.toString());
            }}
            className="form-grid"
            style={{ gap: "0.75rem" }}
          >
            <input type="hidden" name="valuation_model_id" value={modelId} />

            <SelectField id="scenario" label="Scenario" name="scenario" required>
              <option value="Base">Base Case</option>
              <option value="Bull">Bull Case</option>
              <option value="Bear">Bear Case</option>
            </SelectField>

            <TextField id="discount_rate" label="Discount Rate (WACC)" name="discount_rate" type="number" step="0.001" defaultValue="0.10" required />
            <TextField id="terminal_growth_rate" label="Terminal Growth Rate" name="terminal_growth_rate" type="number" step="0.001" defaultValue="0.025" required />
            <TextField id="projection_years" label="Projection Years" name="projection_years" type="number" defaultValue="5" required />

            <div style={{ paddingTop: "0.75rem", borderTop: "1px solid var(--border-color)" }}>
              <strong style={{ fontSize: "0.85rem" }}>Cash Flow Inputs</strong>
            </div>

            <TextField id="current_fcf" label="Current FCF (Year 0)" name="current_fcf" type="number" step="0.01" required />
            <TextField id="fcf_growth_rate" label="FCF Growth Rate" name="fcf_growth_rate" type="number" step="0.001" defaultValue="0.05" required />
            <TextField id="shares_outstanding" label="Shares Outstanding" name="shares_outstanding" type="number" step="0.01" required />
            <TextField id="net_debt" label="Net Debt" name="net_debt" type="number" step="0.01" defaultValue="0" required />

            <div className="button-row">
              <button type="submit">Run Scenario</button>
            </div>
          </form>
        </Panel>

        {/* Right: Results */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {assumptions.length === 0 ? (
            <Panel title="Scenarios & Outputs">
              <EmptyState label="No scenarios have been run for this model. Fill in the inputs and run a scenario." />
            </Panel>
          ) : (
            assumptions.map((aset) => {
              const output = aset.outputs?.[0];
              const aj = aset.assumptions_json as { current_fcf?: number; shares_outstanding?: number; net_debt?: number; fcf_growth_rate?: number };

              return (
                <Panel key={aset.id} title="">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      <ScenarioBadge scenario={aset.scenario} />
                      <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                        WACC: {(aset.discount_rate * 100).toFixed(1)}% · Terminal: {(aset.terminal_growth_rate * 100).toFixed(1)}% · {aset.projection_years} years
                      </span>
                    </div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      {new Date(aset.created_at).toLocaleString()}
                    </span>
                  </div>

                  {/* Key Metrics */}
                  <section className="metric-grid" style={{ marginBottom: "1rem" }}>
                    <div className="metric">
                      <div className="metric-label">Implied Share Price</div>
                      <div className="metric-value" style={{ color: "var(--accent)" }}>
                        {output?.implied_share_price != null ? `$${fmt(output.implied_share_price)}` : "—"}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Enterprise Value</div>
                      <div className="metric-value">
                        {output?.enterprise_value != null ? fmtLarge(output.enterprise_value) : "—"}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Equity Value</div>
                      <div className="metric-value">
                        {output?.equity_value != null ? fmtLarge(output.equity_value) : "—"}
                      </div>
                    </div>
                  </section>

                  {/* Assumptions Summary */}
                  <div style={{ display: "flex", gap: "2rem", fontSize: "0.8rem", color: "var(--text-secondary)", padding: "0.5rem 0", borderTop: "1px solid var(--border-color)" }}>
                    <span>FCF: {aj.current_fcf != null ? fmtLarge(aj.current_fcf) : "—"}</span>
                    <span>Growth: {aj.fcf_growth_rate != null ? `${(aj.fcf_growth_rate * 100).toFixed(1)}%` : "—"}</span>
                    <span>Shares: {aj.shares_outstanding?.toLocaleString() ?? "—"}</span>
                    <span>Net Debt: {aj.net_debt != null ? fmtLarge(aj.net_debt) : "—"}</span>
                  </div>

                  {/* Year-by-Year Projection Table */}
                  {output && (
                    <details style={{ marginTop: "0.75rem" }}>
                      <summary style={{ cursor: "pointer", fontSize: "0.85rem", fontWeight: 600, color: "var(--accent)" }}>
                        View Year-by-Year Projections
                      </summary>
                      <ProjectionTable output={output} aset={aset} />
                    </details>
                  )}
                </Panel>
              );
            })
          )}
        </div>
      </div>
    </>
  );
}
