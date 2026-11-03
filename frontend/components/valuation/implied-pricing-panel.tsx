import type { ImpliedPricingBasis } from "@/lib/api";
import { pricingRows } from "@/lib/implied-pricing";

export function ImpliedPricingPanel({ basis, blocked }: {
  basis: ImpliedPricingBasis | null | undefined;
  blocked: boolean;
}) {
  const rows = pricingRows(basis, blocked);
  const secondary = { color: "var(--text-secondary)" };
  return <section aria-label="DCF implied pricing" style={{ padding: "1.25rem", minWidth: 0, overflowWrap: "anywhere", background: "var(--panel-bg)", border: "1px solid var(--line)", borderRadius: "8px", lineHeight: 1.5 }}>
    <h3>DCF implied pricing</h3>
    <p style={secondary}>Calculation from saved User Assumptions. Unsaved form edits are not used.</p>
    {!rows.length ? <p>Reconciled pricing basis is not available. Save and calculate a valid assumption set, then reload.</p> : <>
      <p style={secondary}>Assumption set #{basis?.assumptionSetId ?? "unavailable"}</p>
      <details>
        <summary>Calculation timestamps</summary>
        <p>DCF output: {basis?.outputCreatedAt ?? "Not available"}<br />Saved inputs updated: {basis?.assumptionsUpdatedAt ?? "Not available"}</p>
      </details>
      <dl>
        {rows.map((method) => <div key={method.field} style={{ padding: "0.75rem 0", borderBottom: "1px solid var(--line)" }}>
          <dt>{method.label}</dt>
          <dd style={{ margin: 0 }}><strong>{method.display}</strong>
          {method.reason && <p style={{ ...secondary, margin: "0.25rem 0" }}>{method.reason}</p>}
          <details>
            <summary>Formula and input basis</summary>
            <p>{method.formula}</p>
            <p>Numerator: {method.numerator ?? "Not available"}<br />Denominator: {method.denominator ?? "Not available"}</p>
            <p style={secondary}>Source fields: {method.sourceFields.join(", ")}</p>
          </details>
          </dd>
        </div>)}
      </dl>
      <p style={secondary}>{basis?.note}</p>
    </>}
  </section>;
}
