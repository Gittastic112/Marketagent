"use client";

import React, { useState } from "react";
import {
  runOptionEligibilityTest,
  calculateRealOption,
  OptionEligibilityTestRequest,
  RealOptionCalculateRequest,
  OptionEligibilityTestResponse,
  RealOptionCalculateResponse
} from "@/lib/api";

interface RealOptionsPanelProps {
  valuationId: string;
  baseDcfValue: number;
}

export function RealOptionsPanel({ valuationId, baseDcfValue }: RealOptionsPanelProps) {
  // Eligibility State
  const [eligibilityInputs, setEligibilityInputs] = useState<OptionEligibilityTestRequest>({
    valuation_id: valuationId,
    option_type: "call",
    has_underlying_asset: false,
    has_finite_life: false,
    has_clear_exercise_price: false,
    has_asymmetric_payoff: false,
    has_exclusivity: false,
    can_estimate_volatility: false,
    can_estimate_underlying_value: false
  });

  const [eligibilityResult, setEligibilityResult] = useState<OptionEligibilityTestResponse | null>(null);
  const [isTestingEligibility, setIsTestingEligibility] = useState(false);
  const [overrideEligibility, setOverrideEligibility] = useState(false);

  // Calculation State
  const [calcInputs, setCalcInputs] = useState<RealOptionCalculateRequest>({
    valuation_id: valuationId,
    option_type: "call",
    underlying_asset_value: 0,
    exercise_price: 0,
    option_life_years: 0,
    risk_free_rate: 0.04,
    volatility: 0.30,
    dividend_yield_or_cost_of_delay: 0,
    exclusivity_score: 1.0,
    is_already_counted: false,
    base_dcf_value: baseDcfValue
  });

  const [calcResult, setCalcResult] = useState<RealOptionCalculateResponse | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  const handleTestEligibility = async () => {
    setIsTestingEligibility(true);
    try {
      const res = await runOptionEligibilityTest(eligibilityInputs);
      setEligibilityResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsTestingEligibility(false);
    }
  };

  const handleCalculate = async () => {
    setIsCalculating(true);
    try {
      const res = await calculateRealOption(calcInputs);
      setCalcResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsCalculating(false);
    }
  };

  const canShowEngine = overrideEligibility || (eligibilityResult?.eligibilityPassed);

  return (
    <div className="space-y-8 max-w-4xl">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md p-6">
        <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
          Step 1: Real Option Eligibility Gate
        </h3>
        <p className="text-sm text-slate-500 mb-6">
          Real options should be an advanced add-on, not a default valuation crutch.
          Check the criteria below to see if your asset mathematically qualifies.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-6">
          {Object.keys(eligibilityInputs).filter(k => k.startsWith("has_") || k.startsWith("can_")).map((key) => (
            <label key={key} className="flex items-start space-x-3">
              <input
                type="checkbox"
                className="mt-1"
                checked={eligibilityInputs[key as keyof OptionEligibilityTestRequest] as boolean}
                onChange={(e) => setEligibilityInputs({...eligibilityInputs, [key]: e.target.checked})}
              />
              <span className="text-slate-700 dark:text-slate-300">
                {key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </label>
          ))}
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={handleTestEligibility}
            disabled={isTestingEligibility}
            className="px-4 py-2 bg-slate-800 text-white rounded hover:bg-slate-700 disabled:opacity-50 text-sm"
          >
            {isTestingEligibility ? "Testing..." : "Run Eligibility Test"}
          </button>
          <label className="flex items-center space-x-2 text-sm text-slate-500">
            <input
              type="checkbox"
              checked={overrideEligibility}
              onChange={(e) => setOverrideEligibility(e.target.checked)}
            />
            <span>Override Gate</span>
          </label>
        </div>

        {eligibilityResult && (
          <div className={`mt-6 p-4 rounded-md border ${
            eligibilityResult.eligibilityPassed ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800' : 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800'
          }`}>
            <div className="flex justify-between items-center mb-2">
              <span className="font-semibold text-slate-900 dark:text-slate-100">
                Score: {eligibilityResult.eligibilityScore}/100
              </span>
              <span className={`text-xs font-medium uppercase px-2 py-1 rounded ${
                eligibilityResult.eligibilityPassed ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
              }`}>
                {eligibilityResult.eligibilityPassed ? "Passed" : "Failed"}
              </span>
            </div>
            <p className="text-sm text-slate-700 dark:text-slate-300 mb-2">
              Recommendation: <strong>{eligibilityResult.recommendation.replace(/_/g, " ")}</strong>
            </p>
            {eligibilityResult.warnings.length > 0 && (
              <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-400">
                {eligibilityResult.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            )}
          </div>
        )}
      </div>

      {canShowEngine && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md p-6">
          <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
            Step 2: Black-Scholes Engine
          </h3>
          <p className="text-sm text-slate-500 mb-6">
            Input parameters for the underlying asset to compute its option-adjusted value.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-6">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Underlying Asset Value (S)</label>
              <input
                type="number" step="0.01" className="w-full border rounded p-2 text-sm dark:bg-slate-800 dark:border-slate-700"
                value={calcInputs.underlying_asset_value}
                onChange={e => setCalcInputs({...calcInputs, underlying_asset_value: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Exercise Price (K)</label>
              <input
                type="number" step="0.01" className="w-full border rounded p-2 text-sm dark:bg-slate-800 dark:border-slate-700"
                value={calcInputs.exercise_price}
                onChange={e => setCalcInputs({...calcInputs, exercise_price: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Option Life in Years (t)</label>
              <input
                type="number" step="0.1" className="w-full border rounded p-2 text-sm dark:bg-slate-800 dark:border-slate-700"
                value={calcInputs.option_life_years}
                onChange={e => setCalcInputs({...calcInputs, option_life_years: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Risk-Free Rate (r)</label>
              <input
                type="number" step="0.001" className="w-full border rounded p-2 text-sm dark:bg-slate-800 dark:border-slate-700"
                value={calcInputs.risk_free_rate}
                onChange={e => setCalcInputs({...calcInputs, risk_free_rate: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Volatility (sigma)</label>
              <input
                type="number" step="0.01" className="w-full border rounded p-2 text-sm dark:bg-slate-800 dark:border-slate-700"
                value={calcInputs.volatility}
                onChange={e => setCalcInputs({...calcInputs, volatility: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Dividend Yield (y)</label>
              <input
                type="number" step="0.001" className="w-full border rounded p-2 text-sm dark:bg-slate-800 dark:border-slate-700"
                value={calcInputs.dividend_yield_or_cost_of_delay}
                onChange={e => setCalcInputs({...calcInputs, dividend_yield_or_cost_of_delay: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Exclusivity Score (0-1)</label>
              <input
                type="number" step="0.1" min="0" max="1" className="w-full border rounded p-2 text-sm dark:bg-slate-800 dark:border-slate-700"
                value={calcInputs.exclusivity_score}
                onChange={e => setCalcInputs({...calcInputs, exclusivity_score: parseFloat(e.target.value) || 1})}
              />
            </div>
          </div>

          <label className="flex items-center space-x-3 mb-6 text-sm">
            <input
              type="checkbox"
              checked={calcInputs.is_already_counted}
              onChange={(e) => setCalcInputs({...calcInputs, is_already_counted: e.target.checked})}
            />
            <span className="text-slate-700 dark:text-slate-300">
              Is this value already assumed in your Base DCF growth rate?
            </span>
          </label>

          <button
            onClick={handleCalculate}
            disabled={isCalculating}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 text-sm w-full md:w-auto"
          >
            {isCalculating ? "Pricing Option..." : "Calculate Real Option Value"}
          </button>

          {calcResult && (
            <div className="mt-8 border-t border-slate-200 dark:border-slate-800 pt-6">
              <h4 className="font-medium text-slate-900 dark:text-slate-100 mb-4">Calculation Results</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-6">
                <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded">
                  <div className="text-slate-500 text-xs mb-1">Raw Option Value</div>
                  <div className="font-semibold">${calcResult.raw_option_value.toFixed(2)}</div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded">
                  <div className="text-slate-500 text-xs mb-1">Adjusted Option Value</div>
                  <div className="font-semibold">${calcResult.adjusted_option_value.toFixed(2)}</div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded">
                  <div className="text-slate-500 text-xs mb-1">N(d1) / Delta</div>
                  <div className="font-semibold">{calcResult.option_delta.toFixed(4)}</div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded">
                  <div className="text-slate-500 text-xs mb-1">Option-Adjusted Intrinsic Value</div>
                  <div className="font-semibold text-indigo-600 dark:text-indigo-400">
                    ${calcResult.option_adjusted_intrinsic_value?.toFixed(2)}
                  </div>
                </div>
              </div>

              {calcResult.warnings.length > 0 && (
                <div className="p-3 bg-yellow-50 text-yellow-800 border border-yellow-200 rounded text-sm dark:bg-yellow-900/30 dark:border-yellow-800 dark:text-yellow-200">
                  <ul className="list-disc list-inside">
                    {calcResult.warnings.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
