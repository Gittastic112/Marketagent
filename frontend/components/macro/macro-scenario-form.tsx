import { SelectField, TextField } from "@/components/form-fields";

export function MarketControls({ market, country, sic }: { market: string; country: string; sic: string }) {
  return (
    <>
      <SelectField defaultValue={market} id="market" label="Market" name="market">
        <option value="IN">India</option>
        <option value="US">United States</option>
      </SelectField>
      <TextField defaultValue={country} id="country" label="Country" name="country" />
      <TextField defaultValue={sic} id="sic" label="SIC" name="sic" placeholder="5311" required />
    </>
  );
}

export function MacroScenarioForm({
  market,
  country,
  sic,
  values,
}: {
  market: string;
  country: string;
  sic: string;
  values: Record<string, string>;
}) {
  return (
    <form className="form-grid" method="get">
      <input name="tab" type="hidden" value="scenario" />
      <input name="run" type="hidden" value="scenario" />
      <MarketControls country={country} market={market} sic={sic} />
      <TextField defaultValue={values.rate_shock || "0.01"} id="rate_shock" label="Rate Shock" name="rate_shock" step="0.0001" type="number" />
      <TextField defaultValue={values.gdp_shock || "0"} id="gdp_shock" label="GDP Shock" name="gdp_shock" step="0.0001" type="number" />
      <TextField defaultValue={values.inflation_shock || "0"} id="inflation_shock" label="Inflation Shock" name="inflation_shock" step="0.0001" type="number" />
      <TextField defaultValue={values.currency_shock || "0"} id="currency_shock" label="Currency Shock" name="currency_shock" step="0.0001" type="number" />
      <TextField defaultValue={values.currency_variable_direction || ""} id="currency_variable_direction" label="Currency Direction" name="currency_variable_direction" placeholder="stronger_usd" />
      <div className="button-row">
        <button type="submit">Run Scenario</button>
      </div>
    </form>
  );
}
