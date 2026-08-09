from app.models.dcf import DcfAssumptionSet, DcfOutput
from app.services.dcf import calculate_dcf
from app.api.schemas import DcfOutputRead, DcfScenarioOutput
import copy
from datetime import UTC, datetime

class ScenarioEngine:
    @staticmethod
    def run_scenarios(base_set: DcfAssumptionSet) -> list[DcfScenarioOutput]:
        scenarios = []

        def clone_assumption_set() -> DcfAssumptionSet:
            new_set = DcfAssumptionSet()
            for col in base_set.__table__.columns:
                setattr(new_set, col.name, getattr(base_set, col.name))

            if new_set.revenue_growth_years_json:
                new_set.revenue_growth_years_json = copy.deepcopy(new_set.revenue_growth_years_json)
            return new_set

        def add_scenario(name: str, desc: str, modified_set: DcfAssumptionSet):
            output, _, _ = calculate_dcf(modified_set)

            # Since these are transient and not committed to DB, provide dummy values for schema validation
            output.id = -1
            output.created_at = datetime.now(UTC)

            scenarios.append(DcfScenarioOutput(
                scenario_name=name,
                description=desc,
                output=DcfOutputRead.model_validate(output)
            ))

        # 1. Base Case
        add_scenario("Base Case", "Your saved assumption set without any modifications.", clone_assumption_set())

        # 2. Bull Case
        bull = clone_assumption_set()
        if bull.revenue_growth_years_json:
            for k in bull.revenue_growth_years_json:
                bull.revenue_growth_years_json[k] = str(float(bull.revenue_growth_years_json[k]) + 0.02)
        bull.target_operating_margin = (bull.target_operating_margin or 0.1) + 0.02
        add_scenario("Bull Case", "Higher growth (+2%) and improved margins (+200 bps).", bull)

        # 3. Bear Case
        bear = clone_assumption_set()
        if bear.revenue_growth_years_json:
            for k in bear.revenue_growth_years_json:
                bear.revenue_growth_years_json[k] = str(float(bear.revenue_growth_years_json[k]) - 0.02)
        bear.target_operating_margin = (bear.target_operating_margin or 0.1) - 0.02
        add_scenario("Bear Case", "Lower growth (-2%) and compressed margins (-200 bps).", bear)

        # 4. Recession Shock
        recession = clone_assumption_set()
        if recession.revenue_growth_years_json:
            if "1" in recession.revenue_growth_years_json:
                recession.revenue_growth_years_json["1"] = "0.0"
            if "2" in recession.revenue_growth_years_json:
                recession.revenue_growth_years_json["2"] = "0.0"
        add_scenario("Recession Shock", "Zero growth for the first 2 projection years.", recession)

        # 5. Rate Shock
        rate_shock = clone_assumption_set()
        rate_shock.wacc_start = (rate_shock.wacc_start or 0.1) + 0.02
        rate_shock.wacc_terminal = (rate_shock.wacc_terminal or 0.1) + 0.02
        add_scenario("Rate Shock", "Cost of capital increases by 200 bps across the board.", rate_shock)

        # 6. Margin Compression
        margin_shock = clone_assumption_set()
        margin_shock.target_operating_margin = max(0.01, (margin_shock.target_operating_margin or 0.1) - 0.04)
        add_scenario("Margin Compression", "Target operating margin compressed by 400 bps.", margin_shock)

        return scenarios
