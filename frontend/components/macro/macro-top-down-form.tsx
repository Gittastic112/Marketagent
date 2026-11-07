import { SelectField, TextField } from "@/components/form-fields";
import { macroPeriodCount } from "@/lib/macro-workbench";

const FIELDS = [
  ["operating_income", "Operating income", "0.01"], ["market_cap", "Market cap", "0.01"],
  ["total_debt", "Total debt", "0.01"], ["rate_change", "Rate change (decimal)", "0.0001"],
  ["gdp_growth", "GDP growth (decimal)", "0.0001"], ["inflation_change", "Inflation change (decimal)", "0.0001"],
  ["currency_change", "Currency change (decimal)", "0.0001"],
];

export function MacroTopDownForm({market, country, sic, values}: {
  market: string; country: string; sic: string; values: Record<string, string>;
}) {
  let count = 3;
  try { count = macroPeriodCount(values.period_count); } catch { /* The page displays the invalid-input error. */ }
  return (
    <form className="form-grid" method="get">
      <input name="tab" type="hidden" value="top-down" />
      <input name="market" type="hidden" value={market} />
      <input name="country" type="hidden" value={country} />
      <input name="sic" type="hidden" value={sic} />
      <p className="field field-full muted">Use chronological periods, one reporting currency and consistent units. Enter explicit zeros where intended. Blank inputs cannot establish a sensitivity. Rate changes use decimals: 0.01 means one percentage point.</p>
      <SelectField id="macro-frequency" name="frequency" label="Frequency" defaultValue={values.frequency || "annual"}>
        <option value="annual">Annual</option><option value="quarterly">Quarterly</option>
      </SelectField>
      <TextField id="macro-period-count" name="period_count" label="Number of periods" type="number" min="3" max="24" step="1" defaultValue={count} />
      <div className="button-row field-full"><button type="submit" name="run" value="configure" formNoValidate className="secondary-button">Update period count</button></div>
      {Array.from({length: count}, (_, offset) => offset + 1).map(index => (
        <fieldset className="field field-full" key={index}>
          <legend>Period {index}</legend>
          <div className="form-grid">
            <TextField id={"macro-period-" + index} defaultValue={values["period_" + index] || ""} name={"period_" + index}
              label={"Period " + index + " label"} placeholder="2024 or 2024-Q1" required />
            {FIELDS.map(([key, label, step]) => (
              <TextField key={key} id={"macro-" + key + "-" + index} name={key + "_" + index}
                label={"Period " + index + " " + label} type="number" step={step}
                defaultValue={values[key + "_" + index] ?? ""} required />
            ))}
          </div>
        </fieldset>
      ))}
      <div className="button-row"><button type="submit" name="run" value="top-down">Calculate Top-Down</button></div>
    </form>
  );
}
