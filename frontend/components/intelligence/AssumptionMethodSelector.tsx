"use client";

import React, { useState, useEffect } from "react";
import { fetchApi, postApi } from "@/lib/api";
import { formatPercent } from "@/lib/formatting";

export interface MethodOption {
  method_key: string;
  label: string;
  value?: number;
  low_value?: number;
  base_value?: number;
  high_value?: number;
  unit: string;
  source: {
    source_name: string;
    source_file?: string;
    dataset_date?: string;
  };
  confidence: string;
  available: boolean;
  is_default: boolean;
  notes?: string;
  reason?: string;
}

export interface AssumptionMethodData {
  assumption_key: string;
  country: string;
  industry?: string;
  default_method: string;
  selected_method: string;
  methods: MethodOption[];
  range?: {
    low?: number;
    base?: number;
    high?: number;
  };
  requires_review: boolean;
}

interface AssumptionMethodSelectorProps {
  assumptionKey: string;
  country: string;
  industry?: string;
  valuationId?: number;
  currentValue?: number;
  onMethodSelected: (methodKey: string, value: number, confidence: string, sourceLabel: string) => void;
  label: string;
}

export function AssumptionMethodSelector({
  assumptionKey,
  country,
  industry,
  valuationId,
  currentValue,
  onMethodSelected,
  label,
}: AssumptionMethodSelectorProps) {
  const [methodData, setMethodData] = useState<AssumptionMethodData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<string>("");
  const [customValue, setCustomValue] = useState<string>("");
  const [isCustom, setIsCustom] = useState(false);

  useEffect(() => {
    async function fetchMethods() {
      try {
        setLoading(true);
        let url = `/methods/${assumptionKey}?country=${encodeURIComponent(country)}`;
        if (industry) {
          url += `&industry=${encodeURIComponent(industry)}`;
        }

        const data = await fetchApi<AssumptionMethodData>(url);
        setMethodData(data);

        if (currentValue !== undefined) {
          // Try to match current value to a method, else user_custom
          const matched = data.methods.find((m: MethodOption) => m.value === currentValue && m.available);
          if (matched && matched.method_key !== "user_custom") {
            setSelectedMethod(matched.method_key);
            setIsCustom(false);
          } else {
            setSelectedMethod("user_custom");
            setIsCustom(true);
            setCustomValue((currentValue * 100).toString()); // Assuming percent for now
          }
        } else {
          setSelectedMethod(data.selected_method);
          if (data.selected_method === "user_custom") {
            setIsCustom(true);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    }

    fetchMethods();
  }, [assumptionKey, country, industry, currentValue]);

  const handleMethodChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const key = e.target.value;
    setSelectedMethod(key);

    if (key === "user_custom") {
      setIsCustom(true);
      // Don't fire onMethodSelected until they type something valid
      return;
    }

    setIsCustom(false);

    const method = methodData?.methods.find(m => m.method_key === key);
    if (method && method.value !== undefined) {
      onMethodSelected(
        key,
        method.value,
        method.confidence,
        `${method.label} (${method.source.source_name})`
      );

      if (valuationId) {
        saveMethodSelection(key, method.value, method.confidence, `${method.label} (${method.source.source_name})`);
      }
    }
  };

  const handleCustomValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCustomValue(e.target.value);
    const num = parseFloat(e.target.value);
    if (!isNaN(num)) {
      const val = num / 100; // Assuming percent
      onMethodSelected("user_custom", val, "high", "Custom user input");
    }
  };

  const handleCustomValueBlur = () => {
    const num = parseFloat(customValue);
    if (!isNaN(num) && valuationId) {
      saveMethodSelection("user_custom", num / 100, "high", "Custom user input");
    }
  };

  const saveMethodSelection = async (methodKey: string, value: number, confidence: string, sourceLabel: string) => {
    if (!valuationId) return;

    try {
      await postApi(`/valuations/${valuationId}/select-method`, {
          assumption_key: assumptionKey,
          method_key: methodKey,
          applied_value: value,
          source_label: sourceLabel,
          confidence,
      });
    } catch (err) {
      console.error("Failed to save method selection", err);
    }
  };

  if (loading) return <div className="animate-pulse h-10 bg-muted rounded"></div>;
  if (error) return <div className="text-red-700 text-sm">{error}</div>;
  if (!methodData) return null;

  const currentMethodObj = methodData.methods.find(m => m.method_key === selectedMethod);

  return (
    <div className="flex flex-col gap-2 p-3 bg-card border border-border rounded-md">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-foreground">{label}</label>
        {currentMethodObj && currentMethodObj.confidence && !isCustom && (
          <span className={`text-xs px-2 py-0.5 rounded ${
            currentMethodObj.confidence === 'high' ? 'bg-green-50 text-green-700' :
            currentMethodObj.confidence === 'medium' ? 'bg-amber-50 text-amber-700' :
            'bg-red-50 text-red-700'
          }`}>
            {currentMethodObj.confidence} confidence
          </span>
        )}
      </div>

      <div className="flex gap-2 items-center">
        <select
          className="flex-1 bg-white border border-border text-foreground rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          value={selectedMethod}
          onChange={handleMethodChange}
        >
          {methodData.methods.map(method => (
            <option
              key={method.method_key}
              value={method.method_key}
              disabled={!method.available}
            >
              {method.label}
              {method.available && method.value !== undefined ? ` (${formatPercent(method.value)})` : ` (Unavailable)`}
              {method.is_default ? ' - Default' : ''}
            </option>
          ))}
        </select>

        {isCustom && (
          <div className="relative w-24">
            <input
              type="number"
              step="0.01"
              value={customValue}
              onChange={handleCustomValueChange}
              onBlur={handleCustomValueBlur}
              className="w-full bg-white border border-border text-foreground rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              placeholder="0.00"
            />
            <span className="absolute right-3 top-2 text-muted-foreground text-sm">%</span>
          </div>
        )}
      </div>

      {currentMethodObj && !isCustom && currentMethodObj.source && (
        <div className="text-xs text-muted-foreground flex justify-between">
          <span>Source: {currentMethodObj.source.source_name}</span>
          {currentMethodObj.low_value !== undefined && currentMethodObj.high_value !== undefined && (
             <span>Range: {formatPercent(currentMethodObj.low_value)} - {formatPercent(currentMethodObj.high_value)}</span>
          )}
        </div>
      )}

      {currentMethodObj && currentMethodObj.notes && (
        <div className="text-xs text-muted-foreground italic mt-1 border-t border-border pt-1">
          {currentMethodObj.notes}
        </div>
      )}

      {/* Hidden fields to integrate seamlessly with the HTML form */}
      <input type="hidden" name={assumptionKey} value={isCustom ? (parseFloat(customValue) / 100) : (currentMethodObj?.value ?? "")} />
      <input type="hidden" name={`${assumptionKey}_method`} value={selectedMethod} />
      <input type="hidden" name={`${assumptionKey}_confidence`} value={isCustom ? "high" : (currentMethodObj?.confidence ?? "low")} />
      <input type="hidden" name={`${assumptionKey}_source`} value={isCustom ? "Custom user input" : (currentMethodObj ? `${currentMethodObj.label} (${currentMethodObj.source.source_name})` : "")} />
    </div>
  );
}
