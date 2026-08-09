# Model Selection

Use `data/model_selector.csv` as the machine-readable selector.

## Default
Use the FCFF architecture (`fcffginzu`) for a non-financial operating company when EBIT is positive or can be normalized positive.

## Switch models when needed
- **Young/high-growth, negative EBIT:** use high-growth revenue/margin/reinvestment framework (`higrowth`) rather than forcing a conventional current-EBIT FCFF.
- **Financial services:** prefer equity-side valuation, excess return, dividend/FCFE approaches because debt is part of operations and enterprise reinvestment is hard to define.
- **Mature dividend payer:** dividend discount can be useful when payout policy is meaningful and sustainable.
- **Project/patent with deferral option:** real option (`project`).
- **Distressed/highly levered equity:** equity-as-call (`equity`) and explicit distress probability/recovery where relevant.
- **Relative pricing:** use PE, EV/EBITDA/EBIT, EV/Sales/Price-Sales datasets as a separate pricing layer.

Model choice should follow economics, not data availability convenience.
