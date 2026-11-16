import Link from "next/link";
import type { FinancialExtractionCandidate, SourceFactRevision } from "@/lib/api/financials";
import { ErrorState } from "@/components/page";
import { financialEvidenceHref, financialMetricLabel } from "@/lib/financial-evidence";

export function FinancialSourceHistory({ facts, candidates = [], error }: { facts: SourceFactRevision[] | null; candidates?: FinancialExtractionCandidate[]; error?: string }) {
  const evidence = new Map(candidates.map(candidate => [candidate.id, candidate]));
  const groups = new Map<string, SourceFactRevision[]>();
  for (const fact of facts ?? []) {
    const key = `${fact.effective_at} · ${fact.period_type}`;
    groups.set(key, [...(groups.get(key) ?? []), fact]);
  }
  return (
    <section className="border-y border-gray-200 bg-white px-4 py-5 sm:px-6" aria-labelledby="reviewed-financial-history-title">
      <h2 id="reviewed-financial-history-title" className="text-base font-semibold text-gray-900">Reviewed financial history</h2>
      <p className="mt-1 text-sm text-gray-600">
        Latest recorded revision for each metric and reporting date. These historical facts and calculations retain their own scope;
        they do not certify complete valuation inputs. Open the evidence to inspect the original rows and review limits.
      </p>
      {facts === null ? <ErrorState message={error || "Reviewed financial history could not be loaded. Reload to retry."} /> :
        facts.length === 0 ? <p className="mt-3 text-sm text-gray-600">No reviewed source history is available yet.</p> :
        [...groups.entries()].sort(([a], [b]) => b.localeCompare(a)).map(([period, rows]) => (
          <details className="mt-4 border-t border-gray-200 pt-3" key={period}>
            <summary className="cursor-pointer font-medium">{period}: {rows.length} reviewed entries</summary>
            <div className="mt-3 overflow-x-auto" role="region" aria-label={`Reviewed financial history ${period}`} tabIndex={0}>
              <table className="min-w-full divide-y divide-gray-300 text-sm">
                <thead><tr>
                  <th scope="col" className="py-2 pr-4 text-left">Metric and scope</th>
                  <th scope="col" className="px-3 py-2 text-right">Value</th>
                  <th scope="col" className="px-3 py-2 text-left">Unit</th>
                  <th scope="col" className="px-3 py-2 text-left">Claim type</th>
                  <th scope="col" className="px-3 py-2 text-left">Revision</th>
                  <th scope="col" className="px-3 py-2 text-left">Evidence</th>
                </tr></thead>
                <tbody className="divide-y divide-gray-200">
                  {[...rows].sort((a, b) => a.fact_key.localeCompare(b.fact_key)).map((fact) => {
                    const candidate = evidence.get(fact.financial_candidate_id);
                    const href = candidate?.raw_document_id === fact.raw_document_id && candidate.company_id === fact.company_id
                      ? financialEvidenceHref(candidate) : `/documents/${fact.raw_document_id}/sections?candidate_id=${fact.financial_candidate_id}`;
                    return (
                    <tr key={fact.id}>
                      <th scope="row" className="py-3 pr-4 text-left font-medium" style={{ minWidth: "15rem", maxWidth: "24rem", overflowWrap: "anywhere" }}>{financialMetricLabel(fact.fact_key)}</th>
                      <td className="whitespace-nowrap px-3 py-3 text-right tabular-nums">{Number.isFinite(fact.value) ? fact.value.toLocaleString(undefined, { maximumFractionDigits: 12 }) : "Not available"}</td>
                      <td className="whitespace-nowrap px-3 py-3">{fact.unit || "Unit missing"}</td>
                      <td className="px-3 py-3">{fact.claim_type}</td>
                      <td className="px-3 py-3">Revision {fact.revision_number}<br />Recorded {new Date(fact.observed_at).toLocaleString("en-US")}<br /><span className="text-gray-500">Recorded time is separate from the reporting date.</span></td>
                      <td className="whitespace-nowrap px-3 py-3"><Link href={href} className="text-blue-700 hover:underline">Open evidence</Link></td>
                    </tr>
                  ); })}
                </tbody>
              </table>
            </div>
          </details>
        ))}
    </section>
  );
}
