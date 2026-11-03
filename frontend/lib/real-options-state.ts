import type { SavedRealOptionResponse } from "./api/real-options.ts";
import type { DcfAssumptionSet } from "./api/valuation.ts";
import { buildValuationOutputState, finiteOutput } from "./valuation-output-state.ts";

export function optionNumber(text: string, name: string): number {
  const value = Number(text);
  if (!text.trim() || !Number.isFinite(value)) throw new Error(`Enter an explicit finite ${name}.`);
  return value;
}

export function savedOptionResultUsable(result: SavedRealOptionResponse, saved: DcfAssumptionSet, modelType: string): boolean {
  const state = buildValuationOutputState(saved);
  return !state.blocked && modelType === "fcff_dcf" && result.model_type === modelType
    && result.assumption_set_id === saved.id && result.assumptions_updated_at === saved.updated_at
    && result.output_created_at === saved.outputs?.created_at && result.currency === state.currency
    && result.diluted_shares === saved.diluted_shares && result.diluted_shares > 0
    && result.base_equity_value === saved.outputs?.equity_value
    && result.base_value_per_share === saved.outputs?.intrinsic_value_per_share
    && [result.raw_option_value, result.adjusted_option_value, result.option_value_per_share,
      result.option_adjusted_equity_value, result.option_adjusted_intrinsic_value].every(finiteOutput)
    && /^[a-f0-9]{64}$/.test(result.input_sha256) && Number.isFinite(Date.parse(result.calculated_at))
    && Array.isArray(result.warnings) && result.warnings.every(w => typeof w === "string");
}
