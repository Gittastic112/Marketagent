import Link from "next/link";
import { SelectField, TextField } from "@/components/form-fields";
import { ErrorState } from "@/components/page";
import type { FinancialReviewField, FinancialReviewPlan } from "@/lib/api/financials";

const STATUS: Record<FinancialReviewField["status"], string> = {
  missing: "Find disclosure", ambiguous: "Resolve scope", unit_review: "Resolve units",
  source_review: "Trace recorded value", recorded_with_source: "Source linked",
  promotion_review: "Review promotion", candidate_review: "Review candidates",
};

export function FinancialReviewPlanPanel({report, error, track, year}: {
  report: FinancialReviewPlan | null; error?: string; track: string; year: string;
}) {
  return <section className="panel" aria-labelledby="financial-review-plan-title">
    <div className="panel-header"><h2 id="financial-review-plan-title">Financial review plan</h2></div>
    <div className="panel-content">
      <p>Choose the analysis you are preparing. This checklist identifies the evidence to review; it does not certify a valuation.</p>
      <form className="form-grid" method="get">
        <SelectField id="financial-review-track" name="review_track" label="Review track" defaultValue={track}>
          <option value="operating">Operating company</option>
          <option value="bank_equity">Bank / financial-services equity</option>
          <option value="equity_cash_flow">Equity cash flow and dividends</option>
        </SelectField>
        <TextField id="financial-review-year" name="review_year" label="Latest annual year" type="number" min="1900" max="2100"
          placeholder="Latest stored year" defaultValue={year} />
        <div className="button-row"><button type="submit">Update review plan</button></div>
      </form>
      {!report ? <ErrorState message={error || "Financial review plan could not be loaded. Retry using Update review plan."} /> : <>
        <p className="muted">{report.basis} Sources stored: {report.source_document_count}. Generated {report.generated_at.slice(0, 10)}.</p>
        <div className="button-row">{report.actions.map(action => <Link key={action.href} className="secondary-button" href={action.href} title={action.reason}>{action.label}</Link>)}</div>
        {!report.periods.length ? <p>Add an annual source or choose a target year to start. No financial periods or values have been created.</p> : null}
        {report.truncated ? <p>The evidence exceeds this report’s bounded window. Review the full source records before drawing a completeness conclusion.</p> : null}
        {report.periods.map((period, index) => <details key={period.year} open={index === 0}>
          <summary>FY{period.year}: {period.source_linked_count} of {period.checklist_count} checklist items linked to reviewed sources</summary>
          <p className="muted">Currency: {period.currency || "Not recorded"} · Reporting date: {period.report_date || "Not recorded"}. Linked sources still require scope review.</p>
          {period.notes.length ? <ul>{period.notes.map(note => <li key={note}>{note}</li>)}</ul> : null}
          <div className="table-wrap" tabIndex={0} aria-label={"Financial review checklist for " + period.year}>
            <table><thead><tr><th>Input</th><th>Next step</th><th>Evidence and action</th></tr></thead>
              <tbody>{period.fields.map(field => <tr key={field.metric}>
                <th>{field.label}</th><td>{STATUS[field.status]}</td><td><p>{field.action}</p>
                  {field.source_links.map(source => <Link key={source.candidate_id} href={source.href} className="secondary-button">Source {source.document_id}, candidate {source.candidate_id}</Link>)}
                  {field.candidate_count > field.source_links.length ? <p className="muted">{field.candidate_count} candidate occurrences; first {field.source_links.length} source links shown.</p> : null}
                </td>
              </tr>)}</tbody></table>
          </div>
        </details>)}
        <details><summary>Scope and evidence limits</summary><ul>{report.limitations.map(item => <li key={item}>{item}</li>)}</ul></details>
      </>}
    </div>
  </section>;
}
