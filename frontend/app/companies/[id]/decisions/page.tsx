import { notFound } from "next/navigation";
import Link from "next/link";
import type { Company, DecisionLog, EvidenceLedgerItem, VariantPerception } from "@/lib/api";
import { serverFetchApi, serverFetchApiResponse } from "@/lib/server-api";
import { summarizeApiMetas } from "@/lib/data-state-meta";
import { DataHealthUpdater } from "@/components/providers/data-health-updater";
import { DataStateNotices } from "@/components/ui/data-states";
import { PageHeader, Panel, EmptyState } from "@/components/page";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { RetainedActionForm } from "@/components/retained-action-form";
import { formActionError } from "@/app/actions/shared";

export const dynamic = "force-dynamic";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export default async function DecisionsPage(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const companyId = parseInt(params.id, 10);
  if (isNaN(companyId)) {
    notFound();
  }

  let company: Company;
  try {
    company = await serverFetchApi<Company>(`/companies/${companyId}`);
  } catch {
    notFound();
  }

  const [evidenceRes, perceptionsRes, decisionsRes] = await Promise.all([
    serverFetchApiResponse<EvidenceLedgerItem[]>(`/evidence?company_id=${companyId}`),
    serverFetchApiResponse<VariantPerception[]>(`/variant-perceptions?company_id=${companyId}`),
    serverFetchApiResponse<DecisionLog[]>(`/decisions?company_id=${companyId}`),
  ]);

  const evidence = evidenceRes.data || [];
  const perceptions = perceptionsRes.data || [];
  const decisions = decisionsRes.data || [];

  const dataState = summarizeApiMetas([evidenceRes.meta, perceptionsRes.meta, decisionsRes.meta]);

  return (
    <>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "2rem" }}>
        <PageHeader
          eyebrow={company.ticker}
          title="Decision Intelligence"
          status={`${decisions.length} recorded decisions`}
        />
        <div>
          <Link href={`/companies/${company.id}`} className="secondary-button">&larr; Back to Company</Link>
        </div>
      </div>

      <DataHealthUpdater segment="decisions" isStale={dataState.someStale || dataState.allStale} />
      <DataStateNotices metas={[evidenceRes.meta, perceptionsRes.meta, decisionsRes.meta]} />
      <p>User Assumptions and research notes. Recorded decisions describe your own reasoning and do not place trades.</p>

      <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>

        {/* VARIANT PERCEPTION */}
        <Panel title="Variant Perception">
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: "1.5rem" }}>
            A variant perception is where your belief about the future diverges from what the market currently prices in.
          </p>
          {perceptionsRes.meta?.status !== "success" ? <p role="alert">Variant perceptions are unavailable. Reload to retry.</p> : perceptions.length === 0 ? (
            <EmptyState label="No variant perception defined." />
          ) : (
            <div className="responsive-field-row" style={{ gap: "1.5rem" }}>
              {perceptions.map(vp => (
                <div key={vp.id} style={{ border: "1px solid var(--border-color)", borderRadius: "8px", padding: "1.5rem", background: "var(--surface)" }}>
                  <div className="responsive-field-row" style={{ marginBottom: "1rem" }}>
                    <div>
                      <h4 style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.5rem" }}>Market Belief</h4>
                      <p style={{ margin: 0, fontSize: "0.95rem" }}>{vp.market_belief}</p>
                    </div>
                    <div>
                      <h4 style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.5rem" }}>My Belief</h4>
                      <p style={{ margin: 0, fontSize: "0.95rem", color: "var(--accent)", fontWeight: 500 }}>{vp.my_belief}</p>
                    </div>
                  </div>
                  {vp.what_would_close_the_gap && (
                    <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--line)" }}>
                      <h4 style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.5rem" }}>What Closes the Gap?</h4>
                      <p style={{ margin: 0, fontSize: "0.9rem", color: "var(--text-secondary)" }}>{vp.what_would_close_the_gap}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <div style={{ marginTop: "1.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--line)" }}>
            <h4 style={{ marginBottom: "1rem" }}>Add Variant Perception</h4>
            <RetainedActionForm resetOnSuccess successMessage="Saved." label="Variant perception entry" action={async (data) => {
              "use server";
              const { createVariantPerception } = await import("@/app/actions");
              try {await createVariantPerception(data, companyId.toString()); return {error: null};}
              catch (error) {return formActionError(error);}
            }} className="form-grid" style={{ gridTemplateColumns: "minmax(0, 1fr)" }}>
              <input type="hidden" name="company_id" value={companyId} />
              <div className="responsive-field-row">
                <TextAreaField id="market_belief" name="market_belief" label="Market Belief" required rows={3} placeholder="What is the consensus view?" />
                <TextAreaField id="my_belief" name="my_belief" label="My Belief" required rows={3} placeholder="What is your divergent view?" />
              </div>
              <TextAreaField id="what_would_close_the_gap" name="what_would_close_the_gap" label="What would close the gap?" rows={2} />
              <SelectField id="confidence" name="confidence" label="Confidence Level" defaultValue="Medium">
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </SelectField>
              <div className="button-row">
                <button type="submit">Save Perception</button>
              </div>
            </RetainedActionForm>
          </div>
        </Panel>

        <div className="responsive-field-row" style={{ gap: "2rem" }}>

          {/* EVIDENCE LEDGER */}
          <Panel title="Evidence Ledger">
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: "1.5rem" }}>
              Keep track of data points and events that support or contradict your thesis.
            </p>
            {evidenceRes.meta?.status !== "success" ? <p role="alert">Evidence notes are unavailable. Reload to retry.</p> : evidence.length === 0 ? (
              <EmptyState label="No evidence recorded yet." />
            ) : (
              <div className="brief-list" style={{ marginBottom: "1.5rem" }}>
                {evidence.map(ev => {
                  let badgeColor = "var(--text-muted)";
                  if (ev.effect === "Supports") badgeColor = "var(--success)";
                  if (ev.effect === "Weakens" || ev.effect === "Contradicts") badgeColor = "var(--danger)";

                  return (
                    <div key={ev.id} className="brief-item" style={{ padding: "0.75rem 0", borderBottom: "1px solid var(--line)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.25rem" }}>
                        <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", padding: "2px 6px", borderRadius: "4px", border: `1px solid ${badgeColor}`, color: badgeColor }}>
                          {ev.effect}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{formatDate(ev.date_discovered)}</span>
                      </div>
                      <p style={{ margin: 0, fontSize: "0.95rem" }}>{ev.evidence_text}</p>
                      {ev.source_link && /^https?:\/\//i.test(ev.source_link) && <a href={ev.source_link} target="_blank" rel="noopener noreferrer">Open recorded source</a>}
                    </div>
                  );
                })}
              </div>
            )}

            <RetainedActionForm id="evidence-entry" resetOnSuccess successMessage="Saved." label="Evidence note entry" action={async (data) => {
              "use server";
              const { createEvidenceLedgerItem } = await import("@/app/actions");
              try {await createEvidenceLedgerItem(data, companyId.toString()); return {error: null};}
              catch (error) {return formActionError(error);}
            }} className="form-grid" style={{ gridTemplateColumns: "minmax(0, 1fr)", background: "var(--surface)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
              <input type="hidden" name="company_id" value={companyId} />
              <TextAreaField id="evidence_text" name="evidence_text" label="New Evidence" required rows={2} />
              <TextField id="source_link" name="source_link" label="Source URL (optional)" type="url" />
              <div className="responsive-field-row">
                <SelectField id="effect" name="effect" label="Effect on Thesis" defaultValue="Supports">
                  <option value="Supports">Supports</option>
                  <option value="Weakens">Weakens</option>
                  <option value="Contradicts">Contradicts</option>
                  <option value="Neutral">Neutral</option>
                </SelectField>
                <TextField id="date_discovered" name="date_discovered" label="Date Discovered" type="date" defaultValue={new Date().toISOString().split('T')[0]} required />
              </div>
              <div className="button-row">
                <button type="submit" className="secondary-button">Add Evidence</button>
              </div>
            </RetainedActionForm>
          </Panel>

          {/* DECISION LOG */}
          <Panel title="Decision Log">
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: "1.5rem" }}>
              Record every major decision (Buy, Sell, Hold) and the exact rationale at that moment.
            </p>
            {decisionsRes.meta?.status !== "success" ? <p role="alert">Decisions are unavailable. Reload to retry.</p> : decisions.length === 0 ? (
              <EmptyState label="No decisions recorded." />
            ) : (
              <div className="brief-list" style={{ marginBottom: "1.5rem" }}>
                {decisions.map(d => {
                  let badgeColor = "var(--text-primary)";
                  if (d.decision_type === "Buy") badgeColor = "var(--success)";
                  if (d.decision_type === "Sell" || d.decision_type === "Trim") badgeColor = "var(--danger)";

                  return (
                    <div key={d.id} className="brief-item" style={{ padding: "0.75rem 0", borderBottom: "1px solid var(--line)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.25rem" }}>
                        <span style={{ fontSize: "0.85rem", fontWeight: 700, color: badgeColor }}>
                          {d.decision_type.toUpperCase()}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{formatDate(d.created_at)}</span>
                      </div>
                      <p style={{ margin: 0, fontSize: "0.95rem" }}>{d.rationale}</p>
                      {d.price_at_time !== null && d.price_at_time !== undefined && (
                        <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                          Recorded price: {d.price_at_time.toFixed(2)} (currency not recorded)
                        </p>
                      )}

                      {/* Review Section */}
                      {d.outcome_review ? (
                        <div style={{ marginTop: "1rem", padding: "1rem", backgroundColor: "var(--surface)", borderLeft: "4px solid var(--accent)" }}>
                          <h4 style={{ fontSize: "0.8rem", textTransform: "uppercase", marginBottom: "0.5rem" }}>Outcome Review</h4>
                          <p style={{ margin: 0, fontSize: "0.9rem" }}>{d.outcome_review.what_happened}</p>
                          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
                            {d.outcome_review.thesis_wrong && <span style={{ fontSize: "0.75rem", background: "var(--danger-bg)", color: "var(--danger)", padding: "2px 6px", borderRadius: "4px" }}>Thesis Wrong</span>}
                            {d.outcome_review.valuation_wrong && <span style={{ fontSize: "0.75rem", background: "var(--warning-bg)", color: "var(--warning)", padding: "2px 6px", borderRadius: "4px" }}>Valuation Wrong</span>}
                            {d.outcome_review.timing_wrong && <span style={{ fontSize: "0.75rem", background: "var(--warning-bg)", color: "var(--warning)", padding: "2px 6px", borderRadius: "4px" }}>Timing Wrong</span>}
                            {d.outcome_review.sizing_wrong && <span style={{ fontSize: "0.75rem", background: "var(--warning-bg)", color: "var(--warning)", padding: "2px 6px", borderRadius: "4px" }}>Sizing Wrong</span>}
                          </div>
                        </div>
                      ) : (
                        <div style={{ marginTop: "1rem" }}>
                          <details style={{ fontSize: "0.9rem" }}>
                            <summary style={{ cursor: "pointer", color: "var(--text-secondary)" }}>Review this decision</summary>
                            <RetainedActionForm resetOnSuccess successMessage="Saved." label={`Outcome review for decision ${d.id}`} action={async (data) => {
                              "use server";
                              const { createOutcomeReview } = await import("@/app/actions");
                              try {await createOutcomeReview(data, d.id.toString(), companyId.toString()); return {error: null};}
                              catch (error) {return formActionError(error);}
                            }} style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem", padding: "1rem", border: "1px solid var(--border-color)", borderRadius: "6px" }}>
                              <TextAreaField id={`what_happened_${d.id}`} name="what_happened" label="What Happened?" required rows={2} />
                              <div className="responsive-field-row" style={{ gap: "0.5rem", fontSize: "0.85rem" }}>
                                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><input type="checkbox" name="thesis_wrong" /> Thesis was wrong</label>
                                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><input type="checkbox" name="valuation_wrong" /> Valuation was wrong</label>
                                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><input type="checkbox" name="timing_wrong" /> Timing was wrong</label>
                                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><input type="checkbox" name="sizing_wrong" /> Sizing was wrong</label>
                                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><input type="checkbox" name="information_unavailable_or_misinterpreted" /> Information missed</label>
                              </div>
                              <button type="submit" className="secondary-button" style={{ alignSelf: "flex-start" }}>Save Review</button>
                            </RetainedActionForm>
                          </details>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            <RetainedActionForm resetOnSuccess successMessage="Saved." label="Decision entry" action={async (data) => {
              "use server";
              const { createDecisionLogItem } = await import("@/app/actions");
              try {await createDecisionLogItem(data, companyId.toString()); return {error: null};}
              catch (error) {return formActionError(error);}
            }} className="form-grid" style={{ gridTemplateColumns: "minmax(0, 1fr)", background: "var(--surface)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
              <input type="hidden" name="company_id" value={companyId} />
              <div className="responsive-field-row">
                <SelectField id="decision_type" name="decision_type" label="Decision" defaultValue="Hold">
                  <option value="Buy">Buy</option>
                  <option value="Sell">Sell</option>
                  <option value="Hold">Hold</option>
                  <option value="Trim">Trim</option>
                  <option value="Pass">Pass</option>
                </SelectField>
                <TextField id="price_at_time" name="price_at_time" label="Price at Time (optional; currency is not stored)" type="number" min="0" step="any" />
              </div>
              <TextAreaField id="rationale" name="rationale" label="Rationale" required rows={2} placeholder="Why are you making this decision right now?" />
              <div className="responsive-field-row">
                <TextField id="emotional_state" name="emotional_state" label="Emotional State" placeholder="e.g. FOMO, Convicted, Fearful" />
                <TextField id="alternatives_considered" name="alternatives_considered" label="Alternatives" placeholder="What else could you do?" />
              </div>
              <div className="button-row">
                <button type="submit" style={{ background: "var(--accent)" }}>Record Decision</button>
              </div>
            </RetainedActionForm>
          </Panel>

        </div>
      </div>
    </>
  );
}
