import Link from "next/link";
import type { DatedInputs } from "@/lib/api/dated-inputs";
import { ErrorState } from "@/components/page";
import { formatNumber } from "@/lib/formatting";

const labels = { available: "Source recorded", missing: "Waiting for source", conflict: "Resolve source conflict",
  unavailable_by_date: "Not established by selected date", unit_review: "Review units" };
const value = (v: unknown) => typeof v === "string" || typeof v === "number" ? String(v) : "Not recorded";
const newYorkTime = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York", hour: "numeric", minute: "2-digit", second: "2-digit", timeZoneName: "short",
});

export function DatedFinancialInputs({ report, valuationDate, knowledge, track, error }: {
  report: DatedInputs | null; valuationDate: string; knowledge: string; track: string; error?: string;
}) {
  return <section className="panel panel-content dated-input-review" id="dated-inputs" aria-labelledby="dated-inputs-title">
    <h2 className="text-lg font-semibold" id="dated-inputs-title">Financial inputs by research date</h2>
    <p>Inspect original amounts and source availability before setting model assumptions. This view does not change any facts or saved models.</p>
    <form className="form-grid" method="get">
      <label>Valuation date<input type="date" name="valuation_date" defaultValue={valuationDate} required /></label>
      <label>Knowledge basis<select name="knowledge" defaultValue={knowledge}>
        <option value="available_by_date">Published by end of day in New York</option>
        <option value="latest_recorded">Latest recorded knowledge, including later sources</option>
      </select></label>
      <label>Evidence checklist<select name="review_track" defaultValue={track}>
        <option value="operating">Operating business</option><option value="bank_equity">Bank equity</option>
        <option value="equity_cash_flow">Equity cash flow</option>
      </select></label>
      <button className="primary-button" type="submit">Review this basis</button>
    </form>
    {!report ? <ErrorState message={error || "Dated evidence is unavailable. Reload to retry."} /> : <>
      <p><strong>{report.valuation_date}</strong> · {report.knowledge === "available_by_date" ? "Published by end of day in New York" : "Later knowledge included"}
        {report.truncated ? " · Partial coverage: scan limit reached" : ""}</p>
      <div className="table-wrap" role="region" aria-label="Dated financial inputs" tabIndex={0}>
        <table><thead><tr><th>Input</th><th>Original amount</th><th>Reporting date</th><th>State and evidence</th></tr></thead>
          <tbody>{report.rows.map(row => <tr key={row.metric}>
            <th scope="row">{row.label}</th>
            <td>{row.original_value == null ? "Not selected" : `${formatNumber(row.original_value, 6)} ${row.original_unit || "Unit missing"}`}<br />{row.claim_type}</td>
            <td>{row.effective_at ?? "Not available"}</td>
            <td><strong>{labels[row.status]}</strong>
              {row.conversion && <p>{row.conversion} · Calculation</p>}
              {row.limitations.map(limit => <p key={limit}>{limit}</p>)}
              {row.sources.length > 0 && <details><summary>Inspect {row.sources.length} source revision{row.sources.length === 1 ? "" : "s"}</summary>
                {row.sources.map(source => <article key={source.revision_id} className="dated-source-detail">
                  <h3>Revision {source.revision_number}{source.revision_id === row.selected_revision_id ? " · selected" : ""}</h3>
                  <p>{formatNumber(source.value, 6)} {source.unit || "Unit missing"} · {source.claim_type}</p>
                  <dl>
                    <dt>Period and accounting basis</dt><dd>{value(source.period.scope)} · {value(source.period.start)} to {value(source.period.end)} · {value(source.period.accounting_basis)}</dd>
                    <dt>Publication</dt><dd>{source.publication_date ?? "Unknown"}
                      {source.publication_precision === "timestamp" && source.published_at && <> · <time dateTime={source.published_at}>{newYorkTime.format(new Date(source.published_at))}</time></>}
                      {source.publication_precision === "date" && " · time unreported"} · {source.availability.replaceAll("_", " ")}</dd>
                    <dt>Retrieved / recorded</dt><dd>{source.retrieved_at.slice(0, 10)} / {source.recorded_at.slice(0, 10)}</dd>
                  </dl>
                  {source.period.end_basis === "User Assumption" && <p>Period end was confirmed separately as a User Assumption.</p>}
                  <blockquote>{source.passage}</blockquote>
                  <Link href={source.href}>Open exact source evidence</Link>
                  <details><summary>Source locator</summary><pre>{JSON.stringify(source.locator, null, 2)}</pre></details>
                </article>)}
              </details>}
            </td>
          </tr>)}</tbody>
        </table>
      </div>
      {report.knowledge === "available_by_date" && <Link className="secondary-button" href={`/companies/${report.company_id}/valuation/draft?valuation_date=${report.valuation_date}`}>Review these dated sources in a valuation draft</Link>}
      <details><summary>Basis and limits</summary><ul>{report.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul></details>
    </>}
  </section>;
}
