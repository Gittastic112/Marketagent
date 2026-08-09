import math
from dataclasses import asdict, dataclass
from typing import Any

from app.services.synthetic_rating_catalog import (
    SYNTHETIC_RATING_CATALOG,
    SYNTHETIC_RATING_SOURCE,
    SyntheticRatingFirmType,
)


class CostOfEquityService:
    @staticmethod
    def calculate(
        risk_free_rate: float,
        beta: float,
        mature_erp: float,
        country_risk_premium: float = 0.0,
        lambda_crp: float = 1.0,
    ) -> float:
        """
        Cost of Equity = Risk-free Rate + Beta * Mature Market ERP + Lambda * Country Risk Premium
        """
        return risk_free_rate + (beta * mature_erp) + (lambda_crp * country_risk_premium)


@dataclass(frozen=True, slots=True)
class SyntheticRatingEstimate:
    interest_coverage_ratio: float
    firm_type: SyntheticRatingFirmType
    rating: str
    default_spread: float
    band_lower_bound: float
    band_upper_bound: float
    claim_type: str = "Calculation"
    catalog_version: str = SYNTHETIC_RATING_SOURCE.catalog_version

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["firm_type"] = self.firm_type.value
        return result


class SyntheticRatingService:
    @staticmethod
    def estimate(
        interest_coverage_ratio: float,
        firm_type: SyntheticRatingFirmType | str = SyntheticRatingFirmType.LARGE_NON_FINANCIAL,
    ) -> SyntheticRatingEstimate:
        """Map finite interest coverage to the exact approved workbook table."""
        if not math.isfinite(interest_coverage_ratio):
            raise ValueError("Interest coverage ratio must be finite")

        resolved_type = SyntheticRatingFirmType(firm_type)
        bands = SYNTHETIC_RATING_CATALOG[resolved_type]
        selected_band = bands[0]
        for band in reversed(bands):
            if interest_coverage_ratio >= band.lower_bound:
                selected_band = band
                break

        return SyntheticRatingEstimate(
            interest_coverage_ratio=interest_coverage_ratio,
            firm_type=resolved_type,
            rating=selected_band.rating,
            default_spread=selected_band.default_spread,
            band_lower_bound=selected_band.lower_bound,
            band_upper_bound=selected_band.upper_bound,
        )

    @staticmethod
    def get_rating_and_spread(
        interest_coverage_ratio: float,
        is_large_mfg: bool = True,
    ) -> tuple[str, float]:
        """Compatibility wrapper for the original two-table API."""
        firm_type = (
            SyntheticRatingFirmType.LARGE_NON_FINANCIAL
            if is_large_mfg
            else SyntheticRatingFirmType.SMALL_OR_RISKY
        )
        result = SyntheticRatingService.estimate(
            interest_coverage_ratio,
            firm_type=firm_type,
        )
        return result.rating, result.default_spread


class CostOfDebtService:
    @staticmethod
    def calculate_pre_tax(
        risk_free_rate: float,
        default_spread: float,
        country_default_spread: float = 0.0,
    ) -> float:
        """
        Pre-tax Cost of Debt = Risk-free Rate + Default Spread + Country Default Spread
        """
        return risk_free_rate + default_spread + country_default_spread

    @staticmethod
    def calculate_after_tax(pre_tax_cost: float, marginal_tax_rate: float) -> float:
        """
        After-tax Cost of Debt = Pre-tax Cost of Debt * (1 - Marginal Tax Rate)
        """
        return pre_tax_cost * (1.0 - marginal_tax_rate)


class CapitalStructureService:
    @staticmethod
    def calculate_market_weights(
        market_equity: float,
        total_debt: float,
    ) -> tuple[float, float]:
        """
        Returns Equity Weight, Debt Weight
        """
        total_capital = market_equity + total_debt
        if total_capital <= 0:
            return 1.0, 0.0

        return market_equity / total_capital, total_debt / total_capital


class WaccService:
    @staticmethod
    def calculate_wacc(
        cost_of_equity: float,
        after_tax_cost_of_debt: float,
        equity_weight: float,
        debt_weight: float,
    ) -> float:
        """
        WACC = Cost of Equity * E/(D+E) + After-tax Cost of Debt * D/(D+E)
        """
        return (cost_of_equity * equity_weight) + (after_tax_cost_of_debt * debt_weight)

    @staticmethod
    def calculate_wacc_fade(
        current_wacc: float,
        terminal_wacc: float,
        years_to_fade: int = 5,
        total_years: int = 10,
    ) -> list[float]:
        """
        Returns an array of WACC for each year of the forecast.
        By default, keeps WACC constant for (total_years - years_to_fade), then linear fades to terminal.
        Example: 10 year DCF, 5 year fade: Years 1-5 use current_wacc, Years 6-10 fade linearly to terminal_wacc.
        """
        constant_years = max(0, total_years - years_to_fade)
        wacc_array: list[float] = []

        for i in range(1, total_years + 1):
            if i <= constant_years:
                wacc_array.append(current_wacc)
            else:
                fade_step = i - constant_years
                step_amount = (terminal_wacc - current_wacc) / years_to_fade
                wacc_array.append(round(current_wacc + (step_amount * fade_step), 10))

        return wacc_array
