export function MacroBottomUpForm({
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
      <input name="tab" type="hidden" value="bottom-up" />
      <input name="run" type="hidden" value="bottom-up" />
      <input name="market" type="hidden" value={market} />
      <input name="country" type="hidden" value={country} />
      {[1, 2, 3].map((index) => (
        <div className="field field-full" key={index}>
          <label>Segment {index}</label>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: "0.5rem" }}>
            <input defaultValue={values[`segment_${index}_name`] || (index === 1 ? "Core Segment" : "")} name={`segment_${index}_name`} placeholder="Name" />
            <input defaultValue={values[`segment_${index}_sic`] || (index === 1 ? sic : "")} name={`segment_${index}_sic`} placeholder="SIC" />
            <input defaultValue={values[`segment_${index}_value`] || (index === 1 ? "100" : "")} name={`segment_${index}_value`} placeholder="Value" step="0.01" type="number" />
          </div>
        </div>
      ))}
      <div className="button-row">
        <button type="submit">Calculate Bottom-Up</button>
      </div>
    </form>
  );
}
