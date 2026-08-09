"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ExternalLink } from "lucide-react";
import {
  FinancialExtractionCandidate,
  reviewFinancialCandidate,
  overrideFinancialCandidate,
  promoteFinancialCandidates,
} from "@/lib/api";
import { financialEvidenceHref, financialEvidenceLocatorLabel } from "@/lib/financial-evidence";

export function FinancialCandidateReview({
  initialCandidates,
  companyId,
}: {
  initialCandidates: FinancialExtractionCandidate[];
  companyId: number;
}) {
  const router = useRouter();
  const promotionNoticeKey = `financial-candidate-promotion-${companyId}`;
  const [candidates, setCandidates] = useState(initialCandidates);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<number | "">("");
  const [editUnit, setEditUnit] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const unreviewedCount = candidates.filter((c) => c.review_status === "needs_review").length;
  const canPromote = candidates.some((c) => c.review_status === "reviewed" || c.review_status === "overridden");

  useEffect(() => {
    const storedNotice = window.sessionStorage.getItem(promotionNoticeKey);
    if (storedNotice) {
      setNotice(storedNotice);
      window.sessionStorage.removeItem(promotionNoticeKey);
    }
  }, [promotionNoticeKey]);

  async function handleReview(candidateId: number, status: "needs_review" | "reviewed" | "rejected") {
    try {
      setError(null);
      const updated = await reviewFinancialCandidate(candidateId, status);
      setCandidates(candidates.map((c) => (c.id === candidateId ? updated : c)));
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update status");
    }
  }

  async function handleOverride(candidateId: number) {
    if (typeof editValue !== "number" || !Number.isFinite(editValue) || !editUnit.trim()) return;
    try {
      setError(null);
      const updated = await overrideFinancialCandidate(candidateId, editValue, editUnit.trim());
      setCandidates(candidates.map((c) => (c.id === candidateId ? updated : c)));
      setEditingId(null);
      setEditValue("");
      setEditUnit("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to override value");
    }
  }

  async function handlePromote() {
    setIsSubmitting(true);
    try {
      setError(null);
      setNotice(null);
      const result = await promoteFinancialCandidates(companyId);
      const successMessage = `Successfully promoted ${result.promoted_count} candidates.`;
      window.sessionStorage.setItem(promotionNoticeKey, successMessage);
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to promote candidates");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (candidates.length === 0) {
    return (
      <div className="space-y-4">
        {error ? <p className="text-sm text-red-700" role="alert">{error}</p> : null}
        {notice ? <p className="text-sm text-green-700" role="status">{notice}</p> : null}
        <p className="text-sm text-gray-500">
          No extracted candidates yet. Add or select a filing, then run extraction.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {unreviewedCount > 0 && (
        <div className="rounded-md bg-yellow-50 p-4">
          <div className="flex">
            <div>
              <h3 className="text-sm font-medium text-yellow-800">Review Required</h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  There {unreviewedCount === 1 ? "is" : "are"} {unreviewedCount} extraction{" "}
                  {unreviewedCount === 1 ? "candidate" : "candidates"} that need review before{" "}
                  {unreviewedCount === 1 ? "it can" : "they can"} be promoted.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      {notice ? <p className="text-sm text-green-700" role="status">{notice}</p> : null}

      <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
          <table className="min-w-full divide-y divide-gray-300">
            <thead>
              <tr>
                <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900">Metric</th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Value</th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Year</th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Review Status</th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {candidates.map((candidate) => (
                <tr key={candidate.id}>
                  <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900">
                    {candidate.metric_code.replaceAll("_", " ")}
                    <br />
                    <span className="text-xs font-normal text-gray-500">From: &quot;{candidate.source_text}&quot;</span>
                    <br />
                    <span className="text-xs font-normal text-gray-500">
                      {financialEvidenceLocatorLabel(candidate)}
                    </span>
                    <Link
                      href={financialEvidenceHref(candidate)}
                      target={candidate.source_locator_json?.type === "pdf_table_cell" ? "_blank" : undefined}
                      rel={candidate.source_locator_json?.type === "pdf_table_cell" ? "noopener noreferrer" : undefined}
                      className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:text-blue-900"
                    >
                      Open evidence
                      <ExternalLink aria-hidden="true" size={13} />
                    </Link>
                    {candidate.extraction_warnings ? (
                      <span className="mt-1 block text-xs font-normal text-amber-700">
                        {candidate.extraction_warnings.split(";").join(" / ")}
                      </span>
                    ) : null}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                    {editingId === candidate.id ? (
                      <div className="flex flex-wrap items-center gap-2">
                        <input
                          type="number"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value === "" ? "" : Number(e.target.value))}
                          className="block w-24 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                        />
                        <input
                          type="text"
                          aria-label="Reporting unit"
                          placeholder="e.g. INR crore"
                          value={editUnit}
                          onChange={(e) => setEditUnit(e.target.value)}
                          className="block w-32 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                        />
                        <button
                          onClick={() => handleOverride(candidate.id)}
                          disabled={typeof editValue !== "number" || !Number.isFinite(editValue) || !editUnit.trim()}
                          className="text-xs font-medium text-blue-600 hover:text-blue-500"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => {
                            setEditingId(null);
                            setEditValue("");
                            setEditUnit("");
                          }}
                          className="text-xs font-medium text-gray-600 hover:text-gray-500"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <span>
                        {candidate.value.toLocaleString()} {candidate.unit || "unit missing"}
                      </span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{candidate.fiscal_year ?? "-"}</td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm">
                    <span
                      className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                        candidate.review_status === "reviewed" || candidate.review_status === "overridden"
                          ? "bg-green-50 text-green-700 ring-green-600/20"
                          : candidate.review_status === "rejected"
                          ? "bg-red-50 text-red-700 ring-red-600/10"
                          : "bg-yellow-50 text-yellow-800 ring-yellow-600/20"
                      }`}
                    >
                      {candidate.review_status.replaceAll("_", " ")}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {candidate.review_status === "needs_review" && editingId !== candidate.id && (
                      <div className="flex gap-3">
                        <button
                          onClick={() => {
                            if (!candidate.unit) {
                              setEditingId(candidate.id);
                              setEditValue(candidate.value);
                              setEditUnit("");
                              return;
                            }
                            void handleReview(candidate.id, "reviewed");
                          }}
                          className="text-green-600 hover:text-green-900 font-medium"
                        >
                          {candidate.unit ? "Accept" : "Add unit"}
                        </button>
                        <button
                          onClick={() => handleReview(candidate.id, "rejected")}
                          className="text-red-600 hover:text-red-900 font-medium"
                        >
                          Reject
                        </button>
                        <button
                          onClick={() => {
                            setEditingId(candidate.id);
                            setEditValue(candidate.value);
                            setEditUnit(candidate.unit || "");
                          }}
                          className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                          Override
                        </button>
                      </div>
                    )}
                    {(candidate.review_status === "reviewed" || candidate.review_status === "overridden") && editingId !== candidate.id && (
                       <div className="flex gap-3">
                         <button
                           onClick={() => handleReview(candidate.id, "needs_review")}
                           className="text-gray-600 hover:text-gray-900 font-medium"
                         >
                           Undo
                         </button>
                       </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex justify-end border-t border-gray-200 pt-4">
        <button
          type="button"
          disabled={!canPromote || isSubmitting}
          onClick={handlePromote}
          className={`rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 ${
            (!canPromote || isSubmitting) ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {isSubmitting ? "Promoting..." : "Promote Reviewed Candidates"}
        </button>
      </div>
    </div>
  );
}
