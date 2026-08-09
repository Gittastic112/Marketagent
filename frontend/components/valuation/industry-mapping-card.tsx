"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, FileText, Loader2, Plus, Save, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
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
  const [rows, setRows] = useState<EditorRow[]>([newRow({ weightPercent: 100 })]);
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
  const canSave = validRows && Math.abs(totalWeight - 100) <= 0.01 && !saving;

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
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
          setRows(storedMix.allocations.map((allocation) => newRow({
            segmentName: allocation.segment_name,
            industryName: allocation.industry_name,
            weightPercent: allocation.weight_percent,
            benchmarkAvailability: allocation.benchmark_availability,
          })));
          setAsOfDate(storedMix.as_of_date ?? "");
          setSourceDocumentId(storedMix.source_document_id);
          setNotes(storedMix.notes ?? "");
        } else if (company.damodaran_industry) {
          setRows([newRow({
            segmentName: "Core operations",
            industryName: company.damodaran_industry,
            weightPercent: 100,
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
      setRows(saved.allocations.map((allocation) => newRow({
        segmentName: allocation.segment_name,
        industryName: allocation.industry_name,
        weightPercent: allocation.weight_percent,
        benchmarkAvailability: allocation.benchmark_availability,
      })));
      onConfirmed({ ...company, damodaran_industry: saved.primary_industry });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save industry allocations");
    } finally {
      setSaving(false);
    }
  }

  async function handleAutofill() {
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
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Loading industry allocations...</span>
      </div>
    );
  }

  return (
    <div className="mb-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-medium text-slate-900">Revenue-Weighted Industry Mix</h3>
          <p className="text-sm text-slate-500">Damodaran benchmark allocation for {company.ticker}</p>
        </div>
        {mix && (
          <div className="flex items-center gap-2 text-sm text-green-700">
            <CheckCircle2 className="h-4 w-4" />
            <span>Saved as User Assumption</span>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 flex items-center rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
          <AlertCircle className="mr-2 h-4 w-4" />
          {error}
        </div>
      )}

      {candidates.length > 0 && (
        <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-500">Suggested:</span>
          {candidates.map((candidate) => (
            <Button
              key={candidate.industryName}
              variant="outline"
              size="sm"
              onClick={() => addSuggestedIndustry(candidate.industryName)}
            >
              {candidate.industryName}
            </Button>
          ))}
        </div>
      )}

      <div className="overflow-x-auto">
        <div className="min-w-[800px]">
          <div className="grid grid-cols-[1fr_1.4fr_120px_90px_40px] gap-2 border-b border-slate-200 pb-2 text-xs font-medium uppercase text-slate-500">
            <span>Segment</span>
            <span>Damodaran industry</span>
            <span>Revenue weight</span>
            <span>Coverage</span>
            <span className="sr-only">Remove</span>
          </div>
          {rows.map((row) => (
            <div key={row.key} className="grid grid-cols-[1fr_1.4fr_120px_90px_40px] gap-2 border-b border-slate-100 py-2">
              <input
                className="h-10 min-w-0 rounded-md border border-slate-300 px-3 text-sm"
                aria-label="Segment name"
                value={row.segmentName}
                onChange={(event) => updateRow(row.key, { segmentName: event.target.value })}
              />
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
              <div className="flex h-10 items-center text-xs text-slate-600">
                {row.benchmarkAvailability ? (
                  <span className="tabular-nums">
                    {Object.values(row.benchmarkAvailability).filter(Boolean).length}/
                    {Object.keys(row.benchmarkAvailability).length} modules
                  </span>
                ) : (
                  <span className="text-slate-400">Save to check</span>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="h-10 w-10 px-0"
                title="Remove segment"
                aria-label="Remove segment"
                disabled={rows.length === 1}
                onClick={() => setRows((current) => current.filter((item) => item.key !== row.key))}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <Button variant="outline" size="sm" onClick={() => setRows((current) => [...current, newRow()])}>
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

      {mix?.warnings.length ? (
        <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          <div className="font-medium">Some blended priors are unavailable</div>
          <div className="mt-1">{mix.warnings.slice(0, 2).join(" ")}</div>
          {mix.warnings.length > 2 && <div className="mt-1">+{mix.warnings.length - 2} additional coverage gaps</div>}
        </div>
      ) : null}

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
            <option value="">No source attached</option>
            {sourceDocuments.map((document) => (
              <option key={document.id} value={document.id}>{document.title}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Basis note
          <input
            className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 font-normal"
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

      <div className="mt-4 flex flex-wrap justify-end gap-2">
        <Button onClick={handleSave} disabled={!canSave}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
          Save mix
        </Button>
        <Button variant="outline" onClick={handleAutofill} disabled={!mix || autofilling}>
          {autofilling && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Draft assumptions
        </Button>
      </div>
    </div>
  );
}
