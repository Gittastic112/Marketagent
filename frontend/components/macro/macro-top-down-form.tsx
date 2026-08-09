export function MacroTopDownForm({
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
      <input name="tab" type="hidden" value="top-down" />
      <input name="run" type="hidden" value="top-down" />
      <input name="market" type="hidden" value={market} />
      <input name="country" type="hidden" value={country} />
      <input name="sic" type="hidden" value={sic} />
      {[1, 2, 3].map((index) => (
        <div className="field field-full" key={index}>
          <label>Period {index}</label>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.5rem", marginBottom: "0.5rem" }}>
            <input defaultValue={values[`period_${index}`] || ""} name={`period_${index}`} placeholder="2024" />
            <input defaultValue={values[`operating_income_${index}`] || ""} name={`operating_income_${index}`} placeholder="Operating income" step="0.01" type="number" />
            <input defaultValue={values[`market_cap_${index}`] || ""} name={`market_cap_${index}`} placeholder="Market cap" step="0.01" type="number" />
            <input defaultValue={values[`total_debt_${index}`] || ""} name={`total_debt_${index}`} placeholder="Debt" step="0.01" type="number" />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.5rem" }}>
            <input defaultValue={values[`rate_change_${index}`] || ""} name={`rate_change_${index}`} placeholder="Rate change" step="0.0001" type="number" />
            <input defaultValue={values[`gdp_growth_${index}`] || ""} name={`gdp_growth_${index}`} placeholder="GDP growth" step="0.0001" type="number" />
            <input defaultValue={values[`inflation_change_${index}`] || ""} name={`inflation_change_${index}`} placeholder="Inflation change" step="0.0001" type="number" />
            <input defaultValue={values[`currency_change_${index}`] || ""} name={`currency_change_${index}`} placeholder="Currency change" step="0.0001" type="number" />
          </div>
        </div>
      ))}
      <div className="button-row">
        <button type="submit">Calculate Top-Down</button>
      </div>
    </form>
  );
}
