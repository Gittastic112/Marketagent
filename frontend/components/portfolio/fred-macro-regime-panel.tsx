"use client";

import { useActionState } from "react";

import {
  applyFredMacroRegimeInputWithState,
  type FormActionState,
} from "@/app/actions";
import { EmptyState, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import type { ApiMeta, MarketRegimeMacroProviderRead } from "@/lib/api";


const INITIAL_STATE: FormActionState = { error: null };


export function FredMacroRegimePanel({
  preview,
  meta,
}: {
  preview: MarketRegimeMacroProviderRead | null;
  meta: ApiMeta | null;
}) {
  const [state, formAction, pending] = useActionState(
    applyFredMacroRegimeInputWithState,
    INITIAL_STATE,
  );

  return (
    <Panel title="FRED macro automation">
      <DataStateNotices
        metas={[meta]}
        unavailableMessage="The FRED macro preflight could not be loaded. No provider-backed claim is being shown."
      />
      {!preview ? (
        <EmptyState label="FRED macro automation is unavailable. Check backend readiness and provider health." />
      ) : (
        <div style={{ display: "grid", gap: "0.85rem" }}>
          <div style={{ alignItems: "flex-start", display: "flex", flexWrap: "wrap", gap: "0.75rem", justifyContent: "space-between" }}>
            <div>
              <strong style={{ display: "block" }}>National Financial Conditions Index</strong>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                Claim type: {preview.claim_type}. Provider values are transformed by the disclosed formula.
              </span>
            </div>
            <span className={`badge ${preview.blockers.length ? "badge-outline" : preview.is_stale ? "badge-warning" : "badge-success"}`}>
              {preview.blockers.length ? "Blocked" : preview.applied_input_id ? "Applied" : preview.is_stale ? "Stale input" : "Ready"}
            </span>
          </div>

          <dl style={{ display: "grid", gap: "0.55rem", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", margin: 0 }}>
            <div><dt>FRED value</dt><dd>{preview.observed_value ?? "Unavailable"}</dd></div>
            <div><dt>Calculated score</dt><dd>{preview.normalized_value ?? "Unavailable"}</dd></div>
            <div><dt>Observation date</dt><dd>{preview.as_of_date ?? "Unavailable"}</dd></div>
            <div><dt>Freshness</dt><dd>{preview.age_days === null ? "Unavailable" : `${preview.age_days} days old, limit ${preview.freshness_threshold_days}`}</dd></div>
          </dl>

          <div style={{ color: "var(--text-secondary)", fontSize: "0.82rem", lineHeight: 1.55 }}>
            <div>Macro series record: {preview.macro_series_id ?? "None"}</div>
            <div>Observation record: {preview.observation_id ?? "None"}</div>
            <div>Applied regime input: {preview.applied_input_id ?? "None"}</div>
          </div>

          <p style={{ fontSize: "0.82rem", lineHeight: 1.55, margin: 0 }}>{preview.methodology}</p>
          <a href={preview.source_url} rel="noreferrer" target="_blank" className="text-link">
            Open the official NFCI series on FRED
          </a>

          {preview.blockers.map((blocker) => (
            <p key={blocker} role="status" style={{ color: "var(--danger)", margin: 0 }}>Blocked: {blocker}</p>
          ))}
          {preview.warnings.map((warning) => (
            <p key={warning} role="status" style={{ color: "var(--warning)", margin: 0 }}>Warning: {warning}</p>
          ))}
          {state.error ? <p className="form-error" role="alert">{state.error}</p> : null}

          <div className="button-row">
            <form action={formAction}>
              <button
                className="btn btn-primary"
                type="submit"
                disabled={!preview.can_apply || pending}
              >
                {pending
                  ? "Applying stored observation..."
                  : preview.applied_input_id
                  ? `Already applied as input #${preview.applied_input_id}`
                  : "Apply stored NFCI calculation"}
              </button>
            </form>
            <a className="btn btn-secondary" href="/macro">Import or inspect FRED data</a>
          </div>
          <small style={{ color: "var(--text-secondary)" }}>
            This action creates one source-linked regime input. It does not fetch data, trade, or produce investment advice.
          </small>
        </div>
      )}
    </Panel>
  );
}
