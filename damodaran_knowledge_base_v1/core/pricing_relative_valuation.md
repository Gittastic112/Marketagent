# Pricing and Relative Valuation

Intrinsic valuation and pricing are separate engines.

## Pricing workflow
1. choose a pricing metric consistent with the claim being priced
2. choose genuinely comparable firms/transactions
3. control for the variables that drive the multiple
4. compare market price to the distribution/relationship, not just an average

## Available benchmark families
- `pedata`, `peIndia`: PE and growth-related pricing
- `psdata`, `psIndia`: Price/Sales and EV/Sales
- `vebitda`, `vebitdaIndia`: EV/EBITDA, EV/EBIT, R&D-adjusted variants

## Multiple drivers
Examples:
- PE: expected growth, payout/reinvestment, ROE, equity risk
- EV/Sales: operating margin, growth, reinvestment efficiency, risk
- EV/EBITDA/EBIT: growth, tax, reinvestment, capital intensity, risk

## Forward multiples
Forward multiples are legitimate only when the same horizon and assumptions are used across the comparison set. The farther forward the denominator, the more the multiple embeds a forecast. Always show the forecast needed to reach that denominator.

## Peer discipline
If no clean peer group exists, say so. Do not hand-pick peers or distant forward periods to make a desired price appear reasonable.

## Output
Report intrinsic value and relative pricing separately. A stock can be expensive to intrinsic value while cheap to peers, or the reverse.
