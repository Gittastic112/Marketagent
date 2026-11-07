import { TextField } from "@/components/form-fields";

export function MacroBottomUpForm({market, country, sic, values}: {
  market: string; country: string; sic: string; values: Record<string, string>;
}) {
  return (
    <form className="form-grid" method="get">
      <input name="tab" type="hidden" value="bottom-up" />
      <input name="run" type="hidden" value="bottom-up" />
      <input name="market" type="hidden" value={market} />
      <input name="country" type="hidden" value={country} />
      <p className="field field-full muted">Enter segment values on one currency and valuation basis. Leave unused rows entirely blank. Missing benchmark coefficients stay unavailable.</p>
      {[1, 2, 3].map(index => (
        <fieldset className="field field-full" key={index}>
          <legend>Segment {index}</legend>
          <div className="form-grid">
            <TextField id={"macro-segment-name-" + index} label={"Segment " + index + " name"} name={"segment_" + index + "_name"}
              defaultValue={values["segment_" + index + "_name"] ?? ""} />
            <TextField id={"macro-segment-sic-" + index} label={"Segment " + index + " SIC"} name={"segment_" + index + "_sic"}
              defaultValue={values["segment_" + index + "_sic"] ?? (index === 1 ? sic : "")} />
            <TextField id={"macro-segment-value-" + index} label={"Segment " + index + " value"} name={"segment_" + index + "_value"}
              defaultValue={values["segment_" + index + "_value"] ?? ""} min="0" step="0.01" type="number" />
          </div>
        </fieldset>
      ))}
      <div className="button-row"><button type="submit">Calculate Bottom-Up</button></div>
    </form>
  );
}
