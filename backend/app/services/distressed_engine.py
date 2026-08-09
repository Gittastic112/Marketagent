from app.models.dcf import DcfAssumptionSet, DcfOutput
from copy import deepcopy

class DistressedCompanyEngine:
    @classmethod
    def calculate_distressed_value(cls, assumption_set: DcfAssumptionSet, base_dcf_output: DcfOutput) -> DcfOutput:
        """
        Modifies a standard FCFF DCF output to account for distress probability.
        Value = (1 - P(failure)) * Base_DCF + P(failure) * Distress_Proceeds
        """
        output = deepcopy(base_dcf_output)

        prob_failure = assumption_set.probability_of_failure or 0.0
        distress_proceeds = assumption_set.distress_sale_proceeds or 0.0
        base_value = base_dcf_output.equity_value or 0.0

        if prob_failure <= 0.0:
            output.base_dcf_value = base_value
            return output

        prob_survival = 1.0 - prob_failure
        adjusted_equity_value = (prob_survival * base_value) + (prob_failure * distress_proceeds)

        output.base_dcf_value = base_value
        output.equity_value = adjusted_equity_value

        diluted_shares = assumption_set.diluted_shares or output.diluted_shares or 1.0
        output.intrinsic_value_per_share = adjusted_equity_value / diluted_shares if diluted_shares > 0 else None

        # Adjust EV to match equity value (working backwards)
        # EV = Equity + Debt + MI + PS + Options - Cash - NonOp
        cash = output.cash or 0.0
        non_op = output.non_operating_assets or 0.0
        debt = output.debt or 0.0
        mi = output.minority_interests or 0.0
        ps = output.preferred_stock or 0.0
        options = output.employee_options_value or 0.0

        output.enterprise_value = adjusted_equity_value + debt + mi + ps + options - cash - non_op

        return output
