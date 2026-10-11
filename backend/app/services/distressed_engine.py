from app.models.dcf import DcfAssumptionSet, DcfOutput
from copy import deepcopy
from math import isfinite

from app.schemas.valuation_outputs import DiagnosticWarning


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)

class DistressedCompanyEngine:
    @classmethod
    def calculate_distressed_value(cls, assumption_set: DcfAssumptionSet, base_dcf_output: DcfOutput) -> DcfOutput:
        """
        Modifies a standard FCFF DCF output to account for distress probability.
        Value = (1 - P(failure)) * Base_DCF + P(failure) * Distress_Proceeds
        """
        output = deepcopy(base_dcf_output)

        prob_failure = assumption_set.probability_of_failure
        distress_proceeds = assumption_set.distress_sale_proceeds
        base_value = base_dcf_output.equity_value
        diluted_shares = assumption_set.diluted_shares
        invalid = []
        if not _finite(prob_failure) or not 0 <= prob_failure <= 1:
            invalid.append("probability_of_failure")
        if not _finite(distress_proceeds) or distress_proceeds < 0:
            invalid.append("distress_sale_proceeds")
        if not _finite(diluted_shares) or diluted_shares <= 0:
            invalid.append("diluted_shares")
        if not _finite(base_value):
            invalid.append("base_dcf_value")
        bridge = {}
        for field in ("cash", "cross_holdings", "non_operating_assets", "debt",
                      "operating_leases", "minority_interests", "preferred_stock", "employee_options_value"):
            value = getattr(output, field)
            bridge[field] = 0 if value is None else value
            if not _finite(bridge[field]):
                invalid.append(field)

        def unavailable(fields):
            warning = DiagnosticWarning(severity="blocking", module="distressed_inputs",
                message="Distressed valuation requires finite base equity, explicit probability in [0, 1], nonnegative common-equity recovery and positive shares. No default recovery or share count is inferred.",
                affectedAssumptions=fields,
                suggestedFix="Review recovery after all senior claims in the saved currency and monetary scale.")
            return DcfOutput(assumption_set_id=assumption_set.id,
                warnings_json=[*(base_dcf_output.warnings_json or []), warning.model_dump()],
                model_quality_score=0)

        if invalid:
            return unavailable(invalid)

        prob_survival = 1.0 - prob_failure
        adjusted_equity_value = (prob_survival * base_value) + (prob_failure * distress_proceeds)

        output.base_dcf_value = base_value
        output.equity_value = adjusted_equity_value

        output.diluted_shares = diluted_shares
        output.intrinsic_value_per_share = adjusted_equity_value / diluted_shares
        price = assumption_set.current_market_price
        output.current_market_price = price if _finite(price) and price > 0 else None
        gap = output.intrinsic_value_per_share / price - 1 if output.current_market_price is not None else None
        output.upside_downside_pct = gap if _finite(gap) else None

        # Adjust EV to match equity value (working backwards)
        # EV = Equity + Debt + MI + PS + Options - Cash - NonOp
        output.enterprise_value = (adjusted_equity_value + bridge["debt"] + bridge["operating_leases"]
            + bridge["minority_interests"] + bridge["preferred_stock"] + bridge["employee_options_value"]
            - bridge["cash"] - bridge["cross_holdings"] - bridge["non_operating_assets"])
        if not all(_finite(value) for value in (output.equity_value,
                output.intrinsic_value_per_share, output.enterprise_value)):
            return unavailable(["equity_value", "distress_sale_proceeds", "diluted_shares"])
        # Base forecast/terminal cash flows are survival-case evidence, not a
        # decomposition of probability-weighted equity or enterprise value.
        output.terminal_value_pct_of_ev = None
        output.fcfe_intrinsic_value_per_share = None
        output.ddm_intrinsic_value_per_share = None
        output.warnings_json = [*(base_dcf_output.warnings_json or []), DiagnosticWarning(
            severity="watch", module="distressed_method",
            message="Probability-weighted common-equity estimate. Recovery is assumed after senior claims; base forecast and terminal amounts remain conditional on survival. Supplementary FCFE/DDM and FCFF sensitivity tables are unavailable for this adjusted basis.",
            affectedAssumptions=["probability_of_failure", "distress_sale_proceeds"],
            suggestedFix="Review recovery, currency, scale and the probability assumption; this is not a calibrated failure forecast.").model_dump()]

        return output
