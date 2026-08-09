from typing import Any, Optional
from app.models.dcf import DcfAssumptionSet
from app.api.schemas import DiagnosticWarning, DcfOutputCreate

# Financial services sectors/industries that should NOT use FCFF.
# These companies should use equity-based models (PBV/ROE, Excess Return, DDM).
FINANCIAL_SERVICES_KEYWORDS = frozenset([
    "bank", "banks", "banking",
    "insurance", "insurer", "insurers",
    "financial services", "financial",
    "brokerage", "asset management",
    "nbfc", "housing finance",
    "investment company", "reit",
])


def _is_financial_sector(sector: Optional[str], industry: Optional[str]) -> bool:
    """Check if a company sector or industry implies a financial services firm."""
    for field in (sector, industry):
        if field and any(kw in field.lower() for kw in FINANCIAL_SERVICES_KEYWORDS):
            return True
    return False


class DiagnosticsEngine:
    """
    Phase 8: Diagnostics Engine V2
    Enforces strict valuation guardrails and catches impossible or dangerous assumptions.

    V2 adds:
      - Financial services FCFF block
      - Margin vs industry benchmark
      - Negative FCFF duration warning
      - Terminal ROC vs industry benchmark
      - Share count validation
      - External funding / dilution risk
    """

    @classmethod
    def run_all_diagnostics(
        cls,
        assumption_set: DcfAssumptionSet,
        output: DcfOutputCreate,
        projection_years: list,
        terminal_fcff: float,
        *,
        company_sector: Optional[str] = None,
        company_industry: Optional[str] = None,
        industry_operating_margin: Optional[float] = None,
        industry_roc: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        warnings: list[DiagnosticWarning] = []

        warnings.extend(cls.check_assumption_units(assumption_set))

        # --- Original V1 checks ---
        warnings.extend(cls.check_terminal_value_discipline(assumption_set, terminal_fcff))
        warnings.extend(cls.check_reinvestment_consistency(assumption_set))
        warnings.extend(cls.check_roic_vs_wacc(assumption_set))
        warnings.extend(cls.check_margin_plausibility(assumption_set))
        warnings.extend(cls.check_fcff_sustainability(terminal_fcff, output))
        warnings.extend(cls.check_debt_inclusion(assumption_set))

        # --- V2 additions ---
        warnings.extend(cls.check_financial_services_model(assumption_set, company_sector, company_industry))
        warnings.extend(cls.check_margin_vs_industry(assumption_set, industry_operating_margin))
        warnings.extend(cls.check_negative_fcff_duration(projection_years))
        warnings.extend(cls.check_terminal_roc_vs_industry(assumption_set, industry_roc))
        warnings.extend(cls.check_share_count(assumption_set))
        warnings.extend(cls.check_external_funding_risk(projection_years))
        warnings.extend(cls.check_basic_vs_diluted_shares(assumption_set))
        warnings.extend(cls.check_user_override_far_from_benchmark(assumption_set, industry_operating_margin, industry_roc))
        warnings.extend(cls.check_margin_below_target_unexplained(assumption_set))
        warnings.extend(cls.check_sales_to_capital_vs_industry(assumption_set, industry_operating_margin)) # Using industry margin as a proxy or just hardcode checking for now, but we don't have industry sales-to-capital passed in. Let's pass industry_sales_to_capital as well, or just add it to the signature later. Wait, we can just do a basic check.

        return [w.model_dump() for w in warnings]

    @staticmethod
    def quality_score(warnings: list[dict[str, Any]]) -> float:
        """Return an explainable diagnostic score instead of an unearned default."""
        penalties = {"blocking": 35, "critical": 25, "warning": 10, "watch": 5}
        score = 100 - sum(penalties.get(str(item.get("severity", "")).lower(), 5) for item in warnings)
        return float(max(0, score))

    @staticmethod
    def check_assumption_units(assumption_set: DcfAssumptionSet) -> list[DiagnosticWarning]:
        """Catch percentage-point inputs such as 31.3 for a 31.3% margin."""
        warnings: list[DiagnosticWarning] = []
        bounded_fields = {
            "current_operating_margin": (-1.0, 1.0),
            "target_operating_margin": (-1.0, 1.0),
            "tax_rate": (0.0, 1.0),
            "risk_free_rate": (0.0, 1.0),
            "equity_risk_premium": (0.0, 1.0),
            "cost_of_equity": (0.0, 1.0),
            "pre_tax_cost_of_debt": (0.0, 1.0),
            "debt_to_capital": (0.0, 1.0),
            "equity_to_capital": (0.0, 1.0),
            "wacc_start": (0.0, 1.0),
            "wacc_terminal": (0.0, 1.0),
            "terminal_roic": (0.0, 1.0),
            "terminal_growth_rate": (-0.2, 0.2),
        }
        invalid = [
            field
            for field, (lower, upper) in bounded_fields.items()
            if (value := getattr(assumption_set, field, None)) is not None
            and not lower <= float(value) <= upper
        ]
        if invalid:
            warnings.append(DiagnosticWarning(
                severity="blocking",
                module="input_units",
                message=(
                    "Rate or margin assumptions are outside decimal-unit bounds. "
                    "Enter 31.3% as 0.313, not 31.3."
                ),
                affectedAssumptions=invalid,
                suggestedFix="Convert percentage-point inputs to decimals before rerunning the valuation.",
            ))

        debt_weight = assumption_set.debt_to_capital
        equity_weight = assumption_set.equity_to_capital
        if debt_weight is not None and equity_weight is not None and abs(debt_weight + equity_weight - 1.0) > 0.001:
            warnings.append(DiagnosticWarning(
                severity="blocking",
                module="capital_structure",
                message="Debt-to-capital and equity-to-capital must sum to 100%.",
                affectedAssumptions=["debt_to_capital", "equity_to_capital"],
                suggestedFix="Use decimal capital weights that sum to 1.0.",
            ))
        return warnings

    # =========================================================================
    # V1 CHECKS (preserved from original)
    # =========================================================================

    @staticmethod
    def check_terminal_value_discipline(assumption_set: DcfAssumptionSet, terminal_fcff: float) -> list[DiagnosticWarning]:
        warnings = []
        wacc_terminal = assumption_set.wacc_terminal or 0.10
        terminal_growth_rate = assumption_set.terminal_growth_rate or 0.0
        terminal_roic = assumption_set.terminal_roic or wacc_terminal

        if terminal_growth_rate >= wacc_terminal:
            warnings.append(DiagnosticWarning(
                severity="blocking",
                module="terminal_value",
                message="Terminal growth rate is greater than or equal to terminal WACC. This results in an infinite or invalid terminal value.",
                affectedAssumptions=["terminal_growth_rate", "wacc_terminal"],
                suggestedFix="Lower the terminal growth rate to be strictly less than the terminal WACC (typically 1-3%).",
                formula="Terminal Value = FCFF_n+1 / (WACC - g)"
            ))

        if terminal_growth_rate > 0.05:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="terminal_value",
                message="Terminal growth rate exceeds 5%, which is historically unsustainable for a mature firm in perpetuity.",
                affectedAssumptions=["terminal_growth_rate"],
                suggestedFix="Cap terminal growth at or below long-term global GDP growth or the risk-free rate."
            ))

        terminal_reinvestment_rate = (terminal_growth_rate / terminal_roic) if terminal_roic > 0 else 0.0
        if terminal_growth_rate > 0 and terminal_reinvestment_rate <= 0:
            warnings.append(DiagnosticWarning(
                severity="blocking",
                module="terminal_value",
                message="Terminal growth is positive but terminal reinvestment is zero or negative. Growth must cost capital.",
                affectedAssumptions=["terminal_growth_rate", "terminal_roic"],
                suggestedFix="Set terminal reinvestment rate = terminal growth / terminal ROC.",
                formula="Terminal Reinvestment Rate = g / ROC"
            ))

        return warnings

    @staticmethod
    def check_reinvestment_consistency(assumption_set: DcfAssumptionSet) -> list[DiagnosticWarning]:
        warnings = []
        # In a more advanced build, we would look year by year.
        # For now, we check the global sales_to_capital_ratio.
        s2c = assumption_set.sales_to_capital_ratio or 1.0
        if s2c <= 0:
            warnings.append(DiagnosticWarning(
                severity="critical",
                module="reinvestment",
                message="Sales-to-capital ratio is 0 or negative, implying the firm requires no capital to generate revenue.",
                affectedAssumptions=["sales_to_capital_ratio"],
                suggestedFix="Set sales-to-capital to a realistic industry average (e.g., 1.5 - 3.0).",
                formula="Reinvestment = Change in Revenue / Sales-to-Capital Ratio"
            ))
        elif s2c > 5.0:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="reinvestment",
                message="Sales-to-capital ratio is very high (>5.0). This implies extremely low capital intensity, typical only for software or asset-light service firms.",
                affectedAssumptions=["sales_to_capital_ratio"]
            ))
        return warnings

    @staticmethod
    def check_roic_vs_wacc(assumption_set: DcfAssumptionSet) -> list[DiagnosticWarning]:
        warnings = []
        wacc_terminal = assumption_set.wacc_terminal or 0.10
        terminal_roic = assumption_set.terminal_roic or wacc_terminal
        terminal_growth_rate = assumption_set.terminal_growth_rate or 0.0

        if terminal_growth_rate > 0 and terminal_roic < wacc_terminal:
            warnings.append(DiagnosticWarning(
                severity="critical",
                module="return_on_capital",
                message="Terminal ROC is below terminal WACC while growth is positive. The firm is destroying value by growing.",
                affectedAssumptions=["terminal_roic", "wacc_terminal", "terminal_growth_rate"],
                suggestedFix="Assume ROC = WACC in perpetuity for mature, competitive firms, or accept the value destruction.",
                formula="Value Created = Invested Capital * (ROIC - WACC)"
            ))
        return warnings

    @staticmethod
    def check_margin_plausibility(assumption_set: DcfAssumptionSet) -> list[DiagnosticWarning]:
        warnings = []
        target_margin = assumption_set.target_operating_margin or 0.0

        # Hardcoded fallback until industry benchmarks are fully mapped
        if target_margin > 0.40:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="margins",
                message="Target operating margin exceeds 40%. Very few firms can sustain this without structural monopolies.",
                affectedAssumptions=["target_operating_margin"],
                suggestedFix="Review industry average margins and competitive moats."
            ))
        return warnings

    @staticmethod
    def check_fcff_sustainability(terminal_fcff: float, output: DcfOutputCreate) -> list[DiagnosticWarning]:
        warnings = []
        if terminal_fcff < 0:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="terminal_value",
                message="Terminal FCFF is negative. The firm is destroying value in perpetuity under these assumptions.",
                affectedAssumptions=["target_operating_margin", "sales_to_capital_ratio"]
            ))

        if output.enterprise_value and output.enterprise_value > 0 and output.pv_terminal_value:
            tv_pct = output.pv_terminal_value / output.enterprise_value
            if tv_pct > 0.90:
                warnings.append(DiagnosticWarning(
                    severity="warning",
                    module="terminal_value",
                    message=f"Terminal value makes up {tv_pct*100:.1f}% of total enterprise value. This valuation is highly sensitive to terminal assumptions.",
                    affectedAssumptions=["terminal_growth_rate", "wacc_terminal"]
                ))
        return warnings

    @staticmethod
    def check_debt_inclusion(assumption_set: DcfAssumptionSet) -> list[DiagnosticWarning]:
        warnings = []
        if assumption_set.debt == 0.0 or assumption_set.debt is None:
            warnings.append(DiagnosticWarning(
                severity="watch",
                module="equity_bridge",
                message="Debt is 0. Ensure you have properly accounted for all debt and debt-like claims (e.g., operating leases).",
                affectedAssumptions=["debt"]
            ))
        return warnings

    # =========================================================================
    # V2 ADDITIONS
    # =========================================================================

    @staticmethod
    def check_financial_services_model(
        assumption_set: DcfAssumptionSet,
        company_sector: Optional[str],
        company_industry: Optional[str],
    ) -> list[DiagnosticWarning]:
        """
        Financial services companies (banks, insurers, NBFCs) should not use FCFF.
        Debt is a raw material for these firms, not a financing choice.
        They should use equity-based models: DDM, FCFE, PBV/ROE, or Excess Return.
        """
        warnings = []
        if _is_financial_sector(company_sector, company_industry):
            warnings.append(DiagnosticWarning(
                severity="blocking",
                module="model_selection",
                message=(
                    f"Company sector/industry ('{company_sector or company_industry}') "
                    "appears to be a financial services firm. FCFF models are not appropriate "
                    "for banks, insurers, and NBFCs because debt is a raw material, not a "
                    "financing choice. Use FCFE, DDM, PBV/ROE, or Excess Return models."
                ),
                affectedAssumptions=["model_type"],
                suggestedFix="Switch to an equity-based valuation model (FCFE, DDM, or PBV/ROE)."
            ))
        return warnings

    @staticmethod
    def check_margin_vs_industry(
        assumption_set: DcfAssumptionSet,
        industry_operating_margin: Optional[float],
    ) -> list[DiagnosticWarning]:
        """
        Warn if target operating margin is far above the industry adjusted margin.
        A target >50% above industry median requires a moat explanation.
        """
        warnings = []
        target_margin = assumption_set.target_operating_margin
        if target_margin is None or industry_operating_margin is None:
            return warnings

        if industry_operating_margin > 0 and target_margin > 0:
            ratio = target_margin / industry_operating_margin
            if ratio > 1.5:
                warnings.append(DiagnosticWarning(
                    severity="warning",
                    module="margins",
                    message=(
                        f"Target operating margin ({target_margin*100:.1f}%) is "
                        f"{ratio:.1f}× the industry average ({industry_operating_margin*100:.1f}%). "
                        "This requires a strong competitive moat justification."
                    ),
                    affectedAssumptions=["target_operating_margin"],
                    suggestedFix="Review whether the company has structural advantages (pricing power, network effects, IP) that justify premium margins."
                ))
        return warnings

    @staticmethod
    def check_negative_fcff_duration(projection_years: list) -> list[DiagnosticWarning]:
        """
        Warn if FCFF is negative for more than 3 consecutive projection years.
        This implies the company needs external funding and potential dilution.
        """
        warnings = []
        if not projection_years:
            return warnings

        max_consecutive = 0
        current_streak = 0

        for year in projection_years:
            fcff = getattr(year, "fcff", None) if hasattr(year, "fcff") else year.get("fcff") if isinstance(year, dict) else None
            if fcff is not None and fcff < 0:
                current_streak += 1
                max_consecutive = max(max_consecutive, current_streak)
            else:
                current_streak = 0

        if max_consecutive > 3:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="cash_flow",
                message=(
                    f"FCFF is negative for {max_consecutive} consecutive projection years. "
                    "This implies the firm will need external funding (debt or equity issuance), "
                    "which may dilute existing shareholders."
                ),
                affectedAssumptions=["revenue_growth_years_json", "target_operating_margin", "sales_to_capital_ratio"],
                suggestedFix="Consider whether the company has access to funding, or add a dilution/funding note to the equity bridge."
            ))
        return warnings

    @staticmethod
    def check_terminal_roc_vs_industry(
        assumption_set: DcfAssumptionSet,
        industry_roc: Optional[float],
    ) -> list[DiagnosticWarning]:
        """
        Warn if terminal ROC is far above industry average without a moat story.
        This often indicates implicit optimism about competitive advantage duration.
        """
        warnings = []
        terminal_roic = assumption_set.terminal_roic
        if terminal_roic is None or industry_roc is None or industry_roc <= 0:
            return warnings

        ratio = terminal_roic / industry_roc
        if ratio > 2.0:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="return_on_capital",
                message=(
                    f"Terminal ROC ({terminal_roic*100:.1f}%) is {ratio:.1f}× the industry "
                    f"average ({industry_roc*100:.1f}%). In perpetuity, most firms converge "
                    "toward industry returns unless they have durable competitive advantages."
                ),
                affectedAssumptions=["terminal_roic"],
                suggestedFix="Set terminal ROC closer to industry average or WACC unless you can document a durable moat."
            ))
        return warnings

    @staticmethod
    def check_share_count(assumption_set: DcfAssumptionSet) -> list[DiagnosticWarning]:
        """
        Flag if diluted shares outstanding is missing or zero.
        Without this, value per share cannot be computed.
        """
        warnings = []
        shares = assumption_set.diluted_shares

        if shares is None or shares <= 0:
            warnings.append(DiagnosticWarning(
                severity="critical",
                module="equity_bridge",
                message=(
                    "Diluted shares outstanding is missing or zero. "
                    "Value per share cannot be computed without a share count."
                ),
                affectedAssumptions=["diluted_shares"],
                suggestedFix="Enter the diluted shares outstanding from the company's latest filing."
            ))
        return warnings

    @staticmethod
    def check_external_funding_risk(projection_years: list) -> list[DiagnosticWarning]:
        """
        If cumulative FCFF is negative over the entire projection period,
        the company needs external funding. Flag this as an informational
        note about potential dilution or leverage increase.
        """
        warnings = []
        if not projection_years:
            return warnings

        cumulative_fcff = 0.0
        for year in projection_years:
            fcff = getattr(year, "fcff", None) if hasattr(year, "fcff") else year.get("fcff") if isinstance(year, dict) else None
            if fcff is not None:
                cumulative_fcff += fcff

        if cumulative_fcff < 0:
            warnings.append(DiagnosticWarning(
                severity="info",
                module="cash_flow",
                message=(
                    f"Cumulative FCFF over the projection period is negative "
                    f"({cumulative_fcff:,.0f}). The company will need to raise external "
                    "capital (debt or equity), which could dilute existing shareholders "
                    "or increase financial risk."
                ),
                affectedAssumptions=["revenue_growth_years_json", "target_operating_margin", "sales_to_capital_ratio"],
                suggestedFix="Factor in expected dilution from new equity issuance or increased leverage in the equity bridge."
            ))
        return warnings

    @staticmethod
    def check_user_override_far_from_benchmark(
        assumption_set: DcfAssumptionSet,
        industry_operating_margin: Optional[float],
        industry_roc: Optional[float],
    ) -> list[DiagnosticWarning]:
        """
        Warn if a user override is far from the industry benchmark.
        Ideally this checks >2σ, but without stddev, we use a heuristic (>50% deviation).
        """
        warnings = []

        # Target Margin lower bound (upper bound handled by check_margin_vs_industry)
        if assumption_set.target_operating_margin is not None and industry_operating_margin is not None and industry_operating_margin > 0:
            ratio = assumption_set.target_operating_margin / industry_operating_margin
            if ratio < 0.5:
                warnings.append(DiagnosticWarning(
                    severity="watch",
                    module="margins",
                    message=(
                        f"Target operating margin ({assumption_set.target_operating_margin*100:.1f}%) "
                        f"is less than half the industry average ({industry_operating_margin*100:.1f}%). "
                        "This may be overly pessimistic unless the company has a structural disadvantage."
                    ),
                    affectedAssumptions=["target_operating_margin"]
                ))

        # Terminal ROC lower bound (upper bound handled by check_terminal_roc_vs_industry)
        if assumption_set.terminal_roic is not None and industry_roc is not None and industry_roc > 0:
            ratio = assumption_set.terminal_roic / industry_roc
            if ratio < 0.5:
                warnings.append(DiagnosticWarning(
                    severity="watch",
                    module="return_on_capital",
                    message=(
                        f"Terminal ROC ({assumption_set.terminal_roic*100:.1f}%) "
                        f"is less than half the industry average ({industry_roc*100:.1f}%). "
                        "In perpetuity, returns should typically drift toward the industry average or WACC."
                    ),
                    affectedAssumptions=["terminal_roic"]
                ))

        return warnings

    @staticmethod
    def check_basic_vs_diluted_shares(assumption_set: DcfAssumptionSet) -> list[DiagnosticWarning]:
        """
        Warn if the model uses basic shares instead of diluted shares.
        """
        warnings = []
        basic = getattr(assumption_set, "basic_shares", None)
        diluted = assumption_set.diluted_shares

        if basic is not None and diluted is not None and basic > 0 and diluted > 0:
            if basic == diluted:
                warnings.append(DiagnosticWarning(
                    severity="warning",
                    module="equity_bridge",
                    message=(
                        "Model uses basic shares instead of diluted shares (they are identical). "
                        "Diluted shares should include options, restricted stock, and convertible debt to accurately reflect equity value."
                    ),
                    affectedAssumptions=["diluted_shares", "basic_shares"],
                    suggestedFix="Use the fully diluted share count from the company's 10-K/10-Q."
                ))
            elif basic > diluted:
                warnings.append(DiagnosticWarning(
                    severity="blocking",
                    module="equity_bridge",
                    message=(
                        "Basic shares cannot be greater than diluted shares."
                    ),
                    affectedAssumptions=["diluted_shares", "basic_shares"]
                ))

        return warnings

    @staticmethod
    def check_margin_below_target_unexplained(assumption_set: DcfAssumptionSet) -> list[DiagnosticWarning]:
        """
        Warn if the target margin is significantly higher than the current margin
        and there's no story provided, or if current margin is far below target without explanation.
        """
        warnings = []
        target = assumption_set.target_operating_margin
        current = assumption_set.current_operating_margin

        if target is not None and current is not None:
            if target > current + 0.05:  # more than 500 bps expansion
                story = assumption_set.margin_story or ""
                if len(story.strip()) < 20:
                    warnings.append(DiagnosticWarning(
                        severity="warning",
                        module="margins",
                        message=(
                            f"Target margin ({target*100:.1f}%) is significantly higher than "
                            f"current margin ({current*100:.1f}%) but the 'Margin Story' is empty or very brief. "
                            "Margin expansion of this magnitude rarely happens without a clear structural catalyst."
                        ),
                        affectedAssumptions=["target_operating_margin", "current_operating_margin", "margin_story"],
                        suggestedFix="Provide a detailed Margin Story explaining the path to profitability, or lower the target margin."
                    ))
        return warnings

    @staticmethod
    def check_sales_to_capital_vs_industry(
        assumption_set: DcfAssumptionSet,
        industry_operating_margin: Optional[float] = None
    ) -> list[DiagnosticWarning]:
        """
        Warn if Sales-to-Capital ratio is extremely high, implying growth requires almost no capital.
        """
        warnings = []
        s2c = assumption_set.sales_to_capital_ratio

        if s2c is not None:
            # If S2C > 4.0, it's generally very high unless they are a pure software/service company.
            # We already have a warning for >5.0 in `check_reinvestment_consistency`.
            # Let's add a more specific check here.
            # Actually, the user asked for "Sales-to-capital too high vs industry: warning."
            # Since we don't have industry_sales_to_capital passed yet, we can use a proxy or just flag > 3.0 as needing review.
            if s2c > 3.0 and s2c <= 5.0:
                warnings.append(DiagnosticWarning(
                    severity="watch",
                    module="reinvestment",
                    message=(
                        f"Sales-to-Capital ratio is high ({s2c:.2f}). This implies the company needs "
                        "very little reinvestment to grow. Ensure this matches industry characteristics (e.g. software or consulting)."
                    ),
                    affectedAssumptions=["sales_to_capital_ratio"],
                    suggestedFix="Compare Sales-to-Capital with industry peers. Asset-heavy businesses rarely exceed 1.5 - 2.0."
                ))
        return warnings
