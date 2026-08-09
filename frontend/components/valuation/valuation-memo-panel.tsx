"use client";

import React, { useState, useEffect } from "react";
import { generateValuationMemo, fetchValuationMemo, ValuationMemoResponse } from "@/lib/api";
import { AI_DISCLOSURES } from "@/lib/ai-privacy";

interface ValuationMemoPanelProps {
  valuationId: number;
  scenario: string;
}

export function ValuationMemoPanel({ valuationId, scenario }: ValuationMemoPanelProps) {
  const [memo, setMemo] = useState<ValuationMemoResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [privacyAcknowledged, setPrivacyAcknowledged] = useState(false);

  useEffect(() => {
    loadMemo();
  }, [valuationId, scenario]);

  const loadMemo = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchValuationMemo(valuationId, scenario);
      setMemo(data);
    } catch (err: any) {
      console.error(err);
      // It's okay if not found, we just show empty
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!privacyAcknowledged) return;
    setIsGenerating(true);
    setError(null);
    try {
      const data = await generateValuationMemo(valuationId, scenario);
      setMemo(data);
    } catch (err: any) {
      setError(err.message || "Failed to generate memo. Ensure you have calculated the DCF first.");
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return <div className="p-4 text-slate-500">Loading memo...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100">
            Valuation Memo
          </h3>
          <p className="text-sm text-slate-500">
            Synthesizes your quantitative assumptions and DCF outputs into an analyst report.
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !privacyAcknowledged}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 text-sm"
        >
          {isGenerating ? "Writing..." : memo?.memo_markdown ? "Regenerate Memo" : "Generate Memo"}
        </button>
      </div>

      <label className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
        <input
          type="checkbox"
          checked={privacyAcknowledged}
          onChange={(event) => setPrivacyAcknowledged(event.target.checked)}
        />
        <span>{AI_DISCLOSURES.valuationMemo}</span>
      </label>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 rounded-md text-sm">
          {error}
        </div>
      )}

      {memo && memo.memo_markdown ? (
        <div className="border border-slate-200 dark:border-slate-700 rounded-md overflow-hidden bg-white dark:bg-slate-900">
          <div className="bg-slate-50 dark:bg-slate-800 p-3 border-b border-slate-200 dark:border-slate-700 text-xs text-slate-500 flex justify-between">
            <span>
              {memo.is_mock ? "Mock Data" : `Generated using ${memo.provider_name || "AI"}`} | {memo.confidence_label || "Medium Confidence"}
            </span>
            {memo.created_at && <span>{new Date(memo.created_at).toLocaleString()}</span>}
          </div>
          <div className="p-6 prose dark:prose-invert max-w-none text-sm">
            {/* Extremely simple markdown rendering for safety, or we could use a proper react-markdown package if available */}
            {memo.memo_markdown.split('\\n').map((para, i) => (
              <p key={i} className="mb-4">
                {para.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>').replace(/^# (.*)/g, '<h2 class="text-lg font-bold mt-6">$1</h2>')}
              </p>
            ))}
          </div>
        </div>
      ) : (
        <div className="p-12 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-md text-slate-500">
          No memo generated yet. Complete your DCF valuation and click Generate to write the memo.
        </div>
      )}
    </div>
  );
}
