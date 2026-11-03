"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, FileText, Loader2, Plus, Save, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { industryMixHasEdits, industryWarningText } from "@/lib/industry-mix-display";
import {
  AutofillAssumptionDraft,
  Company,
  CompanyIndustryMix,
  IndustryMappingCandidate,
  draftAutofillAssumptions,
  fetchAllIndustryCandidates,
  fetchIndustryMappingCandidates,
  fetchIndustryMix,
  fetchRawDocumentSummaries,
  RawDocument,
  saveIndustryMix,
} from "@/lib/api";

interface IndustryMappingCardProps {
  company: Company;
  onConfirmed: (company: Company) => void;
  onAutofillDrafted?: (draft: AutofillAssumptionDraft) => void;
}

type EditorRow = {
  key: number;
  segmentName: string;
  industryName: string;
  weightPercent: number;
  benchmarkAvailability?: Record<string, boolean>;
};

let nextRowKey = 1;

function newRow(values: Partial<Omit<EditorRow, "key">> = {}): EditorRow {
  return {
    key: nextRowKey++,
    segmentName: values.segmentName ?? "",
    industryName: values.industryName ?? "",
    weightPercent: values.weightPercent ?? 0,
    benchmarkAvailability: values.benchmarkAvailability,
  };
}

export function IndustryMappingCard({ company, onConfirmed, onAutofillDrafted }: IndustryMappingCardProps) {
  const [candidates, setCandidates] = useState<IndustryMappingCandidate[]>([]);
  const [allIndustries, setAllIndustries] = useState<string[]>([]);
  const [mix, setMix] = useState<CompanyIndustryMix | null>(null);
  const [sourceDocuments, setSourceDocuments] = useState<RawDocument[]>([]);
  const [rows, setRows] = useState<EditorRow[]>([newRow()]);
  const [editing, setEditing] = useState(false);
  const [asOfDate, setAsOfDate] = useState("");
  const [sourceDocumentId, setSourceDocumentId] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [autofilling, setAutofilling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalWeight = useMemo(
    () => rows.reduce((total, row) => total + (Number.isFinite(row.weightPercent) ? row.weightPercent : 0), 0),
    [rows],
  );
  const validRows = rows.every(
    (row) => row.segmentName.trim() && row.industryName && row.weightPercent > 0 && row.weightPercent <= 100,
  );
  const hasEdits = industryMixHasEdits(mix, { rows, asOfDate, sourceDocumentId, notes });
  const canSave = validRows && Math.abs(totalWeight - 100) <= 0.01 && hasEdits && !saving && !autofilling;

  function restoreSavedMix(stored: CompanyIndustryMix) {
    setRows(stored.allocations.map((allocation) => newRow({
      segmentName: allocation.segment_name,
      industryName: allocation.industry_name,
      weightPercent: allocation.weight_percent,
      benchmarkAvailability: allocation.benchmark_availability,
    })));
    setAsOfDate(stored.as_of_date ?? "");
    setSourceDocumentId(stored.source_document_id);
    setNotes(stored.notes ?? "");
  }

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      setMix(null);
      setRows([newRow()]);
      setAsOfDate("");
      setSourceDocumentId(null);
      setNotes("");
      setEditing(false);
      try {
        const country = company.country || "India";
        const [suggestions, industries, storedMix, documents] = await Promise.all([
          fetchIndustryMappingCandidates(company.id, country),
          fetchAllIndustryCandidates(country),
          fetchIndustryMix(company.id),
          fetchRawDocumentSummaries(),
        ]);
        if (cancelled) return;
        setCandidates(suggestions);
        setAllIndustries(industries);
        setSourceDocuments(documents.filter((document) => document.company_id === company.id));
        setMix(storedMix);
        if (storedMix) {
          restoreSavedMix(storedMix);
        } else if (company.damodaran_industry) {
          setRows([newRow({
            industryName: company.damodaran_industry,
          })]);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load industry allocations");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [company.country, company.damodaran_industry, company.id]);

  function updateRow(key: number, patch: Partial<EditorRow>) {
    setRows((current) => current.map((row) => row.key === key ? { ...row, ...patch } : row));
  }

  function addSuggestedIndustry(industryName: string) {
    setRows((current) => {
      const empty = current.find((row) => !row.industryName);
      if (empty) {
        return current.map((row) => row.key === empty.key ? { ...row, industryName } : row);
      }
      return [...current, newRow({ industryName })];
    });
  }

  async function handleSave() {
    if (!canSave) return;
    setSaving(true);
    setError(null);
    try {
      const saved = await saveIndustryMix(company.id, {
        basis: "revenue",
        as_of_date: asOfDate || null,
        source_document_id: sourceDocumentId,
        notes: notes.trim() || null,
        allocations: rows.map((row) => ({
          segment_name: row.segmentName.trim(),
          industry_name: row.industryName,
          weight_percent: row.weightPercent,
        })),
      });
      setMix(saved);
      restoreSavedMix(saved);
      setEditing(false);
      onConfirmed({ ...company, damodaran_industry: saved.primary_industry });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save industry allocations");
    } finally {
      setSaving(false);
    }
  }

  async function handleAutofill() {
    if (!mix || hasEdits || saving) return;
    setAutofilling(true);
    setError(null);
    try {
      const draft = await draftAutofillAssumptions(company.id, {});
      onAutofillDrafted?.(draft);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to draft autofill assumptions");
    } finally {
      setAutofilling(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-600">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Loading industry allocations...</span>
      </div>
    );
  }

  return (
    <section className="industry-mix-card">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-medium text-slate-900">Revenue-Weighted Industry Mix</h3>
          <p className="text-sm text-slate-500">Damodaran benchmark allocation for {company.ticker}</p>
        </div>
        {mix && (
          <div className={`flex items-center gap-2 text-sm ${hasEdits ? "text-amber-700" : "text-green-700"}`}>
            <CheckCircle2 className="h-4 w-4" />
            <span>{hasEdits ? "Unsaved changes" : "Saved as User Assumption"}</span>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 flex items-center rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
          <AlertCircle className="mr-2 h-4 w-4" />
          {error}
        </div>
      )}

      {mix && !editing && (
        <>
          <div className="industry-mix-summary" role="list" aria-label="Saved business mix">
            {mix.allocations.map((allocation, index) => (
              <div className="industry-mix-summary-row" role="listitem" key={allocation.id ?? index}>
                <div><strong>{allocation.segment_name}</strong><span>{allocation.industry_name}</span></div>
                <strong>{allocation.weight_percent.toLocaleString(undefined, { maximumFractionDigits: 2 })}%</strong>
              </div>
            ))}
          </div>
          <div className="industry-mix-summary-actions">
            <span>As of {mix.as_of_date || "date not provided"}. Weights are shown rounded; saved precision is retained.</span>
            <Button variant="outline" className="secondary-button" disabled={saving || autofilling} onClick={() => setEditing(true)}>Edit business mix</Button>
          </div>
          <p className={`text-sm ${mix.coverage_status === "complete" ? "text-green-700" : "text-amber-700"}`}>
            {mix.coverage_status} benchmark coverage
          </p>
          <details className="industry-mix-basis">
            <summary>Basis and source</summary>
            <p>{mix.notes || "No basis note provided."}</p>
            <p>{mix.source_document_id === null
              ? "No uploaded document linked. Consult the basis note for other source references."
              : `Source: ${sourceDocuments.find((document) => document.id === mix.source_document_id)?.title || `Document ${mix.source_document_id} (title unavailable)`}`}</p>
          </details>
        </>
      )}

      {!mix && company.damodaran_industry && (
        <p className="mb-3 text-sm text-slate-600">
          Saved comparison: <strong>{company.damodaran_industry}</strong>. No revenue mix is saved.
          Enter supported business weights before saving a mix; a single-industry comparison does not establish those weights.
        </p>
      )}

      {(editing || !mix) && <fieldset className="industry-mix-edit-fields m-0 min-w-0 border-0 p-0" disabled={saving || autofilling}>
      {candidates.length > 0 && (
        <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-600">Profile text matches, review before use:</span>
          {candidates.map((candidate) => (
            <Button
              key={candidate.industryName}
              variant="outline"
              size="sm"
              className="secondary-button"
              title={candidate.reason}
              onClick={() => addSuggestedIndustry(candidate.industryName)}
            >
              {candidate.industryName}
            </Button>
          ))}
        </div>
      )}

      <div className="industry-mix-editor">
          <div className="industry-mix-header">
            <span>Segment</span>
            <span>Damodaran industry</span>
            <span>Revenue weight</span>
            <span>Coverage</span>
            <span className="sr-only">Remove</span>
          </div>
          {rows.map((row, index) => (
            <div key={row.key} className="industry-mix-row">
              <label className="industry-mix-field industry-mix-segment">
                <span className="industry-mix-field-label">Business segment {index + 1}</span>
              <input
                className="h-10 min-w-0 rounded-md border border-slate-300 px-3 text-sm"
                aria-label="Segment name"
                value={row.segmentName}
                onChange={(event) => updateRow(row.key, { segmentName: event.target.value })}
              />
              </label>
              <label className="industry-mix-field industry-mix-industry">
                <span className="industry-mix-field-label">Industry comparison</span>
              <select
                className="h-10 min-w-0 rounded-md border border-slate-300 bg-white px-3 text-sm"
                aria-label={`Industry for ${row.segmentName || "segment"}`}
                value={row.industryName}
                onChange={(event) => updateRow(row.key, {
                  industryName: event.target.value,
                  benchmarkAvailability: undefined,
                })}
              >
                <option value="">Select industry</option>
                {allIndustries.map((industryName) => (
                  <option key={industryName} value={industryName}>{industryName}</option>
                ))}
              </select>
              </label>
              <label className="industry-mix-field industry-mix-weight">
                <span className="industry-mix-field-label">Share of revenue</span>
                <div className="relative">
                <input
                  className="h-10 w-full rounded-md border border-slate-300 px-3 pr-7 text-right text-sm tabular-nums"
                  aria-label={`Revenue weight for ${row.segmentName || "segment"}`}
                  type="number"
                  min="0.01"
                  max="100"
                  step="0.01"
                  value={row.weightPercent || ""}
                  onChange={(event) => updateRow(row.key, { weightPercent: Number(event.target.value) })}
                />
                <span className="pointer-events-none absolute right-2 top-2.5 text-sm text-slate-500">%</span>
                </div>
              </label>
              <div className="industry-mix-coverage text-xs text-slate-600">
                {row.benchmarkAvailability ? (
                  <span className="tabular-nums">
                    {Object.values(row.benchmarkAvailability).filter(Boolean).length}/
                    {Object.keys(row.benchmarkAvailability).length} benchmark groups
                  </span>
                ) : (
                  <span className="text-slate-600">Save to check</span>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="industry-mix-remove secondary-button"
                title="Remove segment"
                aria-label={`Remove ${row.segmentName || `segment ${index + 1}`}`}
                disabled={rows.length === 1}
                onClick={() => setRows((current) => current.filter((item) => item.key !== row.key))}
              >
                <Trash2 className="h-4 w-4" aria-hidden="true" /> Remove
              </Button>
            </div>
          ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <Button variant="outline" size="sm" className="secondary-button" onClick={() => setRows((current) => [...current, newRow()])}>
          <Plus className="mr-2 h-4 w-4" /> Add segment
        </Button>
        <div className="flex items-center gap-3">
          {mix && (
            <span className={`text-xs font-medium uppercase ${mix.coverage_status === "complete" ? "text-green-700" : "text-amber-700"}`}>
              {mix.coverage_status} benchmark coverage
            </span>
          )}
          <span className={`text-sm font-medium tabular-nums ${Math.abs(totalWeight - 100) <= 0.01 ? "text-green-700" : "text-amber-700"}`}>
            Total {totalWeight.toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="mt-4 grid gap-3 border-t border-slate-200 pt-4 lg:grid-cols-[180px_1fr_1.2fr]">
        <label className="text-sm font-medium text-slate-700">
          As-of date
          <input
            className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 font-normal"
            type="date"
            value={asOfDate}
            onChange={(event) => setAsOfDate(event.target.value)}
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Weight source
          <select
            className="mt-1 h-10 w-full rounded-md border border-slate-300 bg-white px-3 font-normal"
            value={sourceDocumentId ?? ""}
            onChange={(event) => setSourceDocumentId(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">No uploaded document linked</option>
            {sourceDocuments.map((document) => (
              <option key={document.id} value={document.id}>{document.title}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Basis note
          <textarea
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 font-normal"
            rows={3}
            maxLength={1000}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </label>
      </div>

      {mix?.source_document_id && (
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-600">
          <FileText className="h-4 w-4" />
          <span>
            Source: {sourceDocuments.find((document) => document.id === mix.source_document_id)?.title || `Document ${mix.source_document_id}`}
          </span>
        </div>
      )}
      </fieldset>}

      {mix?.warnings.length ? (
        <div className="industry-mix-warnings mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          <div className="font-medium">Some industry benchmarks are unavailable for this mix</div>
          <ul>{mix.warnings.slice(0, 2).map((warning, index) => <li key={index}>{industryWarningText(warning)}</li>)}</ul>
          {mix.warnings.length > 2 && <details>
            <summary>Show {mix.warnings.length - 2} more coverage notes</summary>
            <ul>{mix.warnings.slice(2).map((warning, index) => <li key={index}>{industryWarningText(warning)}</li>)}</ul>
          </details>}
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap justify-end gap-2">
        {editing && mix && <Button variant="outline" className="secondary-button" disabled={saving || autofilling} onClick={() => {
          restoreSavedMix(mix);
          setEditing(false);
          setError(null);
        }}>Cancel edits</Button>}
        {(editing || !mix) &&
        <Button onClick={handleSave} disabled={!canSave}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
          Save mix
        </Button>}
        <Button variant="outline" className="secondary-button" onClick={handleAutofill} disabled={!mix || hasEdits || saving || autofilling}>
          {autofilling && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Draft from saved mix
        </Button>
      </div>
      {mix && hasEdits && <p className="mt-2 text-sm text-amber-800" role="status">Save or cancel your changes before drafting assumptions from this mix.</p>}
    </section>
  );
}
