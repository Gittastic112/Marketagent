"use client";

import React, { useState } from "react";
import { DcfAssumptionSet, runNarrativeToNumbers, NarrativeToNumbersResponse } from "@/lib/api";
import { AI_DISCLOSURES } from "@/lib/ai-privacy";

interface NarrativeToNumbersPanelProps {
  valuationId: number;
  scenario: string;
  currentAssumptions: DcfAssumptionSet;
  onApplyAssumptions: (updates: Partial<DcfAssumptionSet>) => void;
}

export function NarrativeToNumbersPanel({
  valuationId,
  scenario,
  currentAssumptions,
  onApplyAssumptions,
}: NarrativeToNumbersPanelProps) {
  const [narrative, setNarrative] = useState(currentAssumptions.story_text || "");
  const [isGenerating, setIsGenerating] = useState(false);
  const [suggestions, setSuggestions] = useState<NarrativeToNumbersResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [privacyAcknowledged, setPrivacyAcknowledged] = useState(false);

  const handleGenerate = async () => {
    if (!narrative.trim() || !privacyAcknowledged) return;
    setIsGenerating(true);
    setError(null);
    try {
      const res = await runNarrativeToNumbers(valuationId, scenario, { narrative_text: narrative });
      setSuggestions(res);
    } catch (err: any) {
      setError(err.message || "Failed to generate assumptions from narrative.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApplyAll = () => {
    if (!suggestions) return;
    onApplyAssumptions({
      story_text: narrative,
      target_operating_margin: suggestions.target_operating_margin,
      revenue_growth_years_json: suggestions.revenue_growth_years,
      sales_to_capital_ratio: suggestions.sales_to_capital_ratio,
      terminal_growth_rate: suggestions.terminal_growth_rate,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100">
          Narrative to Numbers
        </h3>
        <p className="text-sm text-slate-500">
          Write out your thesis for the company. The AI will extract quantitative assumptions matching your story.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Company Story
          </label>
          <textarea
            className="w-full p-3 border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 min-h-[160px]"
            placeholder="e.g. They are an AI software company scaling rapidly, taking market share from legacy vendors. Margins will expand significantly, but R&D reinvestment will stay high."
            value={narrative}
            onChange={(e) => setNarrative(e.target.value)}
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating || !narrative.trim() || !privacyAcknowledged}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? "Analyzing..." : "Map to Assumptions"}
        </button>

        <label className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input
            type="checkbox"
            checked={privacyAcknowledged}
            onChange={(event) => setPrivacyAcknowledged(event.target.checked)}
          />
          <span>{AI_DISCLOSURES.narrativeToNumbers}</span>
        </label>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 rounded-md text-sm">
            {error}
          </div>
        )}

        {suggestions && (
          <div className="mt-8 border border-slate-200 dark:border-slate-700 rounded-md overflow-hidden bg-white dark:bg-slate-900">
            <div className="bg-slate-50 dark:bg-slate-800 p-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
              <h4 className="font-medium text-slate-900 dark:text-slate-100">
                {suggestions.ai_meta?.is_mock ? "Mock Data: Estimated Assumptions" : "AI Estimated Assumptions"}
              </h4>
              <button
                onClick={handleApplyAll}
                className="px-3 py-1 bg-emerald-600 text-white text-sm rounded-md hover:bg-emerald-700"
              >
                Apply All
              </button>
            </div>
            <div className="divide-y divide-slate-100 dark:divide-slate-800">

              <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="col-span-1">
                  <span className="block text-xs font-medium text-slate-500 uppercase">Target Margin</span>
                  <span className="block text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {(suggestions.target_operating_margin * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="col-span-2 text-sm text-slate-600 dark:text-slate-400 flex items-center">
                  {suggestions.target_operating_margin_reason}
                </div>
              </div>

              <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="col-span-1">
                  <span className="block text-xs font-medium text-slate-500 uppercase">Sales-to-Capital</span>
                  <span className="block text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {suggestions.sales_to_capital_ratio.toFixed(2)}
                  </span>
                </div>
                <div className="col-span-2 text-sm text-slate-600 dark:text-slate-400 flex items-center">
                  {suggestions.sales_to_capital_reason}
                </div>
              </div>

              <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="col-span-1">
                  <span className="block text-xs font-medium text-slate-500 uppercase">Terminal Growth</span>
                  <span className="block text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {(suggestions.terminal_growth_rate * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="col-span-2 text-sm text-slate-600 dark:text-slate-400 flex items-center">
                  {suggestions.terminal_growth_reason}
                </div>
              </div>

              <div className="p-4">
                <span className="block text-xs font-medium text-slate-500 uppercase mb-2">Revenue Growth Path</span>
                <div className="flex gap-2 mb-2">
                  {Object.entries(suggestions.revenue_growth_years).map(([year, rate]) => (
                    <div key={year} className="flex-1 bg-slate-50 dark:bg-slate-800 p-2 rounded text-center border border-slate-200 dark:border-slate-700">
                      <div className="text-xs text-slate-500">Year {year}</div>
                      <div className="font-semibold text-slate-900 dark:text-slate-100">{(rate * 100).toFixed(1)}%</div>
                    </div>
                  ))}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                  {suggestions.revenue_growth_reason}
                </div>
              </div>

            </div>
          </div>
        )}
      </div>
    </div>
  );
}
