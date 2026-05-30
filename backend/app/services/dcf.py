from app.models.dcf import DcfAssumptionSet, DcfOutput

def calculate_dcf(assumption_set: DcfAssumptionSet) -> DcfOutput:
    """
    Deterministically calculates the DCF based on the given assumptions.
    Required keys in assumption_set.assumptions_json:
    - current_fcf (float): Unlevered Free Cash Flow for Year 0.
    - shares_outstanding (float): Total number of shares.
    - net_debt (float): Total debt minus cash.
    - fcf_growth_rate (float or list[float]): Growth rate(s) for the projection period.
    """
    assumptions = assumption_set.assumptions_json
    current_fcf = float(assumptions.get("current_fcf", 0.0))
    shares_outstanding = float(assumptions.get("shares_outstanding", 1.0))
    net_debt = float(assumptions.get("net_debt", 0.0))
    fcf_growth_rate = assumptions.get("fcf_growth_rate", 0.0)

    projection_years = assumption_set.projection_years
    discount_rate = assumption_set.discount_rate
    terminal_growth_rate = assumption_set.terminal_growth_rate

    # Generate FCF projections
    projected_fcfs = []
    pv_of_fcfs = []
    
    last_fcf = current_fcf
    for year in range(1, projection_years + 1):
        if isinstance(fcf_growth_rate, list):
            # If a list of rates is provided, use the corresponding year's rate, or the last one if out of bounds
            rate = fcf_growth_rate[min(year - 1, len(fcf_growth_rate) - 1)]
        else:
            rate = float(fcf_growth_rate)
            
        projected_fcf = last_fcf * (1 + rate)
        projected_fcfs.append(projected_fcf)
        last_fcf = projected_fcf
        
        # Present value of this year's FCF
        discount_factor = (1 + discount_rate) ** year
        pv_fcf = projected_fcf / discount_factor
        pv_of_fcfs.append(pv_fcf)

    # Terminal Value
    terminal_value = last_fcf * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
    pv_terminal_value = terminal_value / ((1 + discount_rate) ** projection_years)
    
    enterprise_value = sum(pv_of_fcfs) + pv_terminal_value
    equity_value = enterprise_value - net_debt
    implied_share_price = equity_value / shares_outstanding if shares_outstanding > 0 else 0.0

    output_json = {
        "projected_fcfs": projected_fcfs,
        "pv_of_fcfs": pv_of_fcfs,
        "terminal_value": terminal_value,
        "pv_terminal_value": pv_terminal_value,
    }

    return DcfOutput(
        assumption_set_id=assumption_set.id,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        implied_share_price=implied_share_price,
        output_json=output_json
    )
