import type { DcfAssumptionSet, DcfScenarioOutput } from "./api.ts";
import { buildValuationOutputState, finiteOutput, outputGap, outputMoney } from "./valuation-output-state.ts";

export function scenarioDisplay(scenarios: DcfScenarioOutput[], assumptions: DcfAssumptionSet, modelType = "fcff_dcf") {
  return scenarios.map(scenario => {
    const state = buildValuationOutputState({ ...assumptions, outputs: scenario.output }, modelType);
    const value = scenario.output.intrinsic_value_per_share;
    return { ...scenario, state, value: outputMoney(value, state), gap: outputGap(state),
      sortValue: !state.blocked && finiteOutput(value) ? value : null };
  }).sort((a, b) => a.sortValue == null ? (b.sortValue == null ? 0 : 1)
    : b.sortValue == null ? -1 : a.sortValue > b.sortValue ? -1 : a.sortValue < b.sortValue ? 1 : 0);
}
