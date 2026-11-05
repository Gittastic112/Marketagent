"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { Panel } from "@/components/page";
import { fetchBriefTriage, type TriageFinding, type TriageSource, type TriageSuggestion } from "@/lib/api/brief-triage";
import { useLatestResource } from "@/lib/use-latest-resource";
import { BriefComparisonReview, dispositionLabels } from "@/components/brief-comparison-review";

function utc(value: string) {
  return new Date(value).toLocaleString("en-US", { timeZone: "UTC", timeZoneName: "short" });
}

export function FindingEvidence({ source, finding, index, suggestion }: {
  source: TriageSource; finding: TriageFinding; index: number; suggestion?: TriageSuggestion;
}) {
  return <article className="triage-evidence">
    <div className="section-intro">
      <span className="badge badge-outline">AI Interpretation</span>
      {source.is_mock && <span className="badge badge-warn">Mock Data</span>}
      <span className="badge badge-outline">Review: {source.review_status.replaceAll("_", " ")}</span>
    </div>
    <h4>{finding.title}</h4>
    <p className="triage-source-line"><Link prefetch={false} href={`/daily-brief/sources/${source.id}#finding-${index}`}>{source.title}</Link>
      <span>Source date: {source.as_of_date || "Unknown"}{finding.page ? ` · PDF page ${finding.page}` : ""}</span></p>
    {suggestion && <p><strong>{suggestion.direction === "review" ? "Review basis" : `Potential ${suggestion.direction}`}</strong> · {suggestion.reason}</p>}
    <blockquote className="brief-source-quote">{finding.quote}</blockquote>
    <p className="muted">{finding.importance} AI importance · {finding.confidence} AI confidence. Exact-passage receipt checked; interpretation not verified.</p>
    <details><summary>Reasoning and provenance</summary>
      <p>{finding.importance_reason}</p>
      <p>{source.provider} / {source.model} · Prompt {source.prompt_version} · AI output #{source.ai_output_id}</p>
      <p>Generated {utc(source.generated_at)}. Stored {utc(source.created_at)}. These are not the source date.</p>
      <p className="brief-source-hash">Source SHA-256: {source.source_sha256}</p>
      <p className="brief-source-hash">AI input hash: {source.input_hash}</p>
      <p>Stored passage characters {finding.start_char}–{finding.end_char} (end exclusive).</p>
      {source.warnings.length > 0 && <ul className="compact-list muted">{source.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>}
      {source.source_kind === "pdf" && <a href={`/api/backend/brief-sources/${source.id}/pdf`} target="_blank" rel="noopener noreferrer">Open original PDF ↗</a>}
    </details>
  </article>;
}

function Comparison({ companyId, includeMock }: { companyId: number; includeMock: boolean }) {
  const loader = useCallback(() => fetchBriefTriage(companyId, includeMock), [companyId, includeMock]);
  const resource = useLatestResource(loader);
  const [field, setField] = useState("");
  const [opposingOnly, setOpposingOnly] = useState(false);
  const [reviewNotice, setReviewNotice] = useState("");
  const data = resource.data;
  const sources = new Map(data?.sources.map(source => [source.id, source]));
  const groups = data?.groups.filter(group => (!field || group.field === field) && (!opposingOnly || group.status === "opposing_directions")) ?? [];

  return <div aria-busy={resource.status === "loading"}>
    <div className="triage-toolbar">
      <button className="btn btn-secondary" disabled={resource.status === "loading"} onClick={() => void resource.reload().catch(() => {})}>Refresh comparison</button>
      <Link prefetch={false} href={`/daily-brief/triage?company_id=${companyId}`}>Company comparison link</Link>
      <p className="muted">Refresh reads stored evidence only. It does not call AI.</p>
    </div>
    {resource.status === "loading" && <p role="status" className="basis-note">Loading the selected company&apos;s source comparison…</p>}
    {resource.status === "error" && <div role="alert" className="basis-note">Comparison unavailable: {resource.error}. No previous comparison is being shown. Use Refresh comparison to retry.</div>}
    {reviewNotice && <p role="status" className="basis-note">{reviewNotice}</p>}
    {data && <>
      <Panel title={`${data.ticker} · Comparison coverage`} className="triage-coverage-panel" actions={<span className="badge badge-outline">Calculation · stored suggestions</span>}>
        <div className="triage-coverage">
          <div><span>Active sources</span><strong>{data.coverage.active_sources}</strong></div>
          <div><span>Sources included</span><strong>{data.coverage.included_sources}</strong></div>
          <div><span>Inputs to inspect</span><strong>{data.groups.length}</strong></div>
          <div><span>Inputs with opposing suggestions</span><strong>{data.groups.filter(group => group.status === "opposing_directions").length}</strong></div>
        </div>
        <p className="muted">{data.coverage.examined_sources} active sources examined · {data.coverage.archived_sources} archived sources excluded · Checked {utc(data.computed_at)}.</p>
        {data.coverage.not_examined > 0 && <p className="basis-note" role="status">Partial coverage: {data.coverage.not_examined} older active sources are outside the newest {data.coverage.source_limit}. Open the source library to inspect them.</p>}
        {Object.keys(data.coverage.excluded).length > 0 && <div className="basis-note"><strong>Other exclusions from this comparison</strong><ul className="compact-list">
          {Object.entries(data.coverage.excluded).map(([reason, count]) => <li key={reason}>{reason === "unusable" ? "Unusable or unverified output" : reason === "mock" ? "Mock Data (not included)" : reason.replaceAll("_", " ")}: {count}</li>)}
        </ul><Link href="/daily-brief" prefetch={false}>Inspect or scan sources in the inbox →</Link></div>}
        <details className="triage-method"><summary>How to read this comparison</summary>
          <ul className="compact-list">{data.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>
          <p className="muted">Method: {data.methodology}. A reviewed AI interpretation is still not an approved financial input.</p>
        </details>
      </Panel>
      {data.reviews.length > 0 && <Panel title="Your latest recorded reviews">
        <p className="muted">Decisions are User Assumptions, not financial-input approvals. Records remain available even when their sources are archived or no longer eligible.</p>
        <ul className="compact-list">{data.reviews.map(review => <li key={review.id}>
          <Link prefetch={false} href={`/daily-brief/triage/reviews/${review.id}`}>{review.field.replaceAll("_", " ")} · {dispositionLabels[review.disposition]} · v{review.version}</Link>
          <span className={`badge ${review.is_current ? "badge-outline" : "badge-warn"}`}>{review.is_current ? "Current evidence basis" : "Evidence changed"}</span>
        </li>)}</ul>
      </Panel>}
      {!data.sources.length ? <Panel title="No eligible findings yet">
        <p>{data.coverage.active_sources ? "The examined active sources have no eligible completed scans for this view." : "This company has no active private sources in your inbox."} Nothing has been inferred.</p>
        <Link className="btn btn-primary" href="/daily-brief" prefetch={false}>Add or inspect research sources</Link>
      </Panel> : <>
        <div className="triage-filters">
          <label>Valuation input<select value={field} onChange={event => setField(event.target.value)}><option value="">All mapped inputs</option>{data.groups.map(group => <option key={group.field} value={group.field}>{group.label}</option>)}</select></label>
          <label className="triage-checkbox"><input type="checkbox" checked={opposingOnly} onChange={event => setOpposingOnly(event.target.checked)} />Only opposing suggestions</label>
        </div>
        <p className="muted">Opposing directions need investigation, not an automatic edit. No detected opposition is not agreement. Dates and forecast horizons may differ.</p>
        {!groups.length && <p role="status" className="basis-note">No mapped inputs match this view. This does not establish agreement or complete source coverage.</p>}
        <div className="triage-groups">{groups.map((group, index) => <details className="triage-group" open={index === 0} key={group.field}>
          <summary><span><strong>{group.label}</strong><small>{group.source_count} source records · {group.distinct_content_count} distinct content hashes · Highest AI importance: {group.highest_importance}</small></span>
            <span className={`badge ${group.status === "no_opposition_detected" ? "badge-outline" : "badge-warn"}`}>
              {group.status === "opposing_directions" ? "Opposing suggestions" : group.status === "mixed_within_content" ? "Mixed within same content" : "No opposition detected"}</span></summary>
          <div className="triage-group-body">
            {group.opposition_basis.length > 0 && <p className="basis-note">Potential increase and decrease suggestions occur across distinct content within {group.opposition_basis.map(basis => basis === "mock_data" ? "Mock Data" : "non-mock sources").join(" and ")}. This is not a verified contradiction.</p>}
            {group.status === "mixed_within_content" && <p className="basis-note">The same content carries opposing suggestions. Inspect the interpretation and reporting periods; duplicate records are not independent evidence.</p>}
            <p className="basis-note">Comparison basis: {group.comparability_status || "unknown"}. Matching quoted labels do not verify a contradiction or corroboration.</p>
            {group.comparability && <dl>{Object.entries(group.comparability).map(([dimension, basis]) => <div className="key-value" key={dimension}><dt>{dimension.replaceAll("_", " ")}</dt><dd>{basis.status}: {basis.labels.join("; ") || "Not supplied"}{basis.missing_count > 0 ? ` · ${basis.missing_count} missing` : ""}</dd></div>)}</dl>}
            <div className="triage-evidence-grid">{group.items.map(item => {
              const source = sources.get(item.source_id)!;
              const finding = source.findings[item.finding_index];
              return <FindingEvidence key={`${item.source_id}-${item.finding_index}-${item.suggestion_index}`} source={source} finding={finding} index={item.finding_index} suggestion={finding.valuation_inputs[item.suggestion_index]} />;
            })}</div>
            <BriefComparisonReview key={`${data.evidence_hash}:${data.reviews.find(review => review.field === group.field)?.version ?? 0}`}
              comparison={data} group={group} latest={data.reviews.find(review => review.field === group.field)} onSaved={async () => {
                setReviewNotice("Analyst review recorded. No AI approval, valuation input or saved model was changed.");
                await resource.reload();
              }} />
            <div className="triage-review-link"><Link className="btn btn-secondary" prefetch={false} href={group.review_href}>Inspect {group.label} in valuation draft →</Link><p className="muted">No comparison suggestion is applied. The draft workspace may initialize a review-required draft if none exists; it does not create a saved valuation.</p></div>
          </div>
        </details>)}</div>
        {data.unmapped_findings.length > 0 && <Panel title="Findings without a mapped valuation input"><p>Retained for context. No field or direction has been invented.</p>
          <div className="triage-evidence-grid">{data.unmapped_findings.map(item => {
            const source = sources.get(item.source_id)!;
            return <FindingEvidence key={`${item.source_id}-${item.finding_index}`} source={source} finding={source.findings[item.finding_index]} index={item.finding_index} />;
          })}</div></Panel>}
      </>}
    </>}
  </div>;
}

export function BriefSourceTriage({ companies, initialCompanyId }: {
  companies: Array<{ id: number; ticker: string; name: string }>; initialCompanyId: number | null;
}) {
  const [companyId, setCompanyId] = useState(initialCompanyId);
  const [includeMock, setIncludeMock] = useState(false);
  return <>
    <Panel title="Comparison scope">
      <div className="triage-filters">
        <label>Company to compare<select value={companyId ?? ""} onChange={event => setCompanyId(Number(event.target.value) || null)}><option value="">Choose a company</option>{companies.map(company => <option key={company.id} value={company.id}>{company.ticker} · {company.name}</option>)}</select></label>
        <label className="triage-checkbox"><input type="checkbox" checked={includeMock} onChange={event => setIncludeMock(event.target.checked)} />Include clearly labeled Mock Data</label>
      </div>
      <p className="muted">Your active private sources only, up to the newest 50 per company. Rejected, revision-required and unverified output is excluded. Reading changes nothing; saving an analyst review records a separate decision only.</p>
    </Panel>
    {companyId ? <Comparison key={`${companyId}:${includeMock}`} companyId={companyId} includeMock={includeMock} />
      : <p className="basis-note">Choose a company to compare its scanned sources by valuation input. No external AI request will be made.</p>}
  </>;
}
