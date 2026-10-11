import type { DcfAssumptionSet, ReverseDcfRequest, ReverseDcfResponse } from "./api/valuation.ts";
import { buildValuationOutputState, finiteOutput } from "./valuation-output-state.ts";

export function reverseDcfRequest(assumptionId: number, parameter: ReverseDcfRequest["target_parameter"], price: string, shares: string): ReverseDcfRequest {
  const positive = (text: string, label: string) => {
    const value = Number(text);
    if (!text.trim() || !Number.isFinite(value) || value <= 0) throw new Error(`${label} must be a positive finite number.`);
    return value;
  };
  return { assumption_set_id: assumptionId, target_parameter: parameter,
    current_market_price: positive(price, "Comparison price"),
    ...(shares.trim() ? { diluted_shares: positive(shares, "Diluted shares") } : {}) };
}

export function reverseDcfResultUsable(response: ReverseDcfResponse, request: ReverseDcfRequest,
  assumptions: DcfAssumptionSet, modelType: string): boolean {
  const state = buildValuationOutputState(assumptions);
  return !state.blocked && response.converged === true
    && response.assumption_set_id === assumptions.id
    && response.assumptions_updated_at === assumptions.updated_at
    && response.target_parameter === request.target_parameter
    && response.currency === state.currency && response.model_type === modelType
    && response.comparison_price === request.current_market_price
    && response.diluted_shares === (request.diluted_shares ?? assumptions.diluted_shares)
    && finiteOutput(response.implied_value) && finiteOutput(response.intrinsic_value_at_implied)
    && finiteOutput(response.price_residual) && Math.abs(response.price_residual) <= 0.01
    && Array.isArray(response.diagnostics)
    && response.diagnostics.every(w => ["info", "watch", "warning"].includes(w.severity));
}
