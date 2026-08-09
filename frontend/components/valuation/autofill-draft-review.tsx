"use client";

import { AlertTriangle, Archive, CheckCircle2, Database, RotateCcw, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";

import type {
  AssumptionProvenance,
  AutofillAssumptionDraft,
  Company,
} from "@/lib/api";
import {
  archiveValuationDraft,
  refreshValuationDraft,
  resetValuationDraftFields,
  updateValuationDraft,
} from "@/lib/api";
import {
  provenanceLabel,
  reviewFieldValueIsValid,
  unresolvedReviewFields,
} from "@/lib/autofill-review";

type DraftReviewProps = {
  company: Company;
  draft: AutofillAssumptionDraft;
  draftId: number;
  initialReviewedFields: string[];
  initialEditedFields: string[];
  initialUpdatedAt: string;
  action: (formData: FormData) => void | Promise<void>;
};

type FieldDefinition = {
  key: string;
  label: string;
};

const FIELD_GROUPS: Array<{ title: string; fields: FieldDefinition[] }> = [
  {
    title: "Operating Assumptions",
    fields: [
      { key: "starting_revenue", label: "Starting Revenue" },
      { key: "current_operating_margin", label: "Current Operating Margin" },
      { key: "target_operating_margin", label: "Target Operating Margin" },
      { key: "tax_rate", label: "Tax Rate" },
      { key: "sales_to_capital_ratio", label: "Sales to Capital Ratio" },
      { key: "starting_invested_capital", label: "Starting Invested Capital" },
    ],
  },
  {
    title: "Discount Rate and Terminal Value",
    fields: [
      { key: "risk_free_rate", label: "Risk-Free Rate" },
      { key: "equity_risk_premium", label: "Equity Risk Premium" },
      { key: "beta", label: "Beta" },
      { key: "cost_of_equity", label: "Cost of Equity" },
      { key: "pre_tax_cost_of_debt", label: "Pre-Tax Cost of Debt" },
      { key: "debt_to_capital", label: "Debt to Capital" },
      { key: "equity_to_capital", label: "Equity to Capital" },
      { key: "wacc_start", label: "Starting WACC" },
      { key: "wacc_terminal", label: "Terminal WACC" },
      { key: "terminal_growth_rate", label: "Terminal Growth Rate" },
      { key: "terminal_roic", label: "Terminal ROIC" },
    ],
  },
  {
    title: "Equity Bridge",
    fields: [
      { key: "cash", label: "Cash" },
      { key: "debt", label: "Debt" },
      { key: "minority_interests", label: "Minority Interests" },
      { key: "preferred_stock", label: "Preferred Stock" },
      { key: "employee_options_value", label: "Employee Options Value" },
      { key: "diluted_shares", label: "Diluted Shares" },
      { key: "current_market_price", label: "Current Market Price" },
    ],
  },
];

const RENDERED_FIELDS = new Set([
  "revenue_growth_years_json",
  ...FIELD_GROUPS.flatMap((group) => group.fields.map((field) => field.key)),
]);

function provenanceEntry(
  value: AssumptionProvenance | string | undefined,
): AssumptionProvenance {
  return typeof value === "object" && value !== null ? value : {};
}

function sourceBadgeClass(entry: AssumptionProvenance): string {
  if (entry.is_placeholder) return "badge badge-warn";
  if (entry.requires_review) return "badge badge-danger";
  return "badge badge-success";
}

export function AutofillDraftReview({
  company,
  draft,
  draftId,
  initialReviewedFields,
  initialEditedFields,
  initialUpdatedAt,
  action,
}: DraftReviewProps) {
  const [values, setValues] = useState<Record<string, unknown>>({ ...draft.assumptions });
  const [reviewedFields, setReviewedFields] = useState<Set<string>>(new Set(initialReviewedFields));
  const [editedFields, setEditedFields] = useState<Set<string>>(new Set(initialEditedFields));
  const [sourceMetadata, setSourceMetadata] = useState(draft.source_metadata);
  const [provenance, setProvenance] = useState(draft.provenance);
  const [warnings, setWarnings] = useState(draft.warnings);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveMessage, setSaveMessage] = useState("");
  const [archiveConfirmationOpen, setArchiveConfirmationOpen] = useState(false);
  const [updatedAt, setUpdatedAt] = useState(initialUpdatedAt);
  const [growthText, setGrowthText] = useState(
    JSON.stringify(draft.assumptions.revenue_growth_years_json ?? {}, null, 2),
  );

  const reviewFields = useMemo(
    () => new Set(sourceMetadata.review_fields),
    [sourceMetadata.review_fields],
  );
  const unresolvedFields = unresolvedReviewFields(
    sourceMetadata,
    reviewedFields,
    values,
  );
  const promotionReady = unresolvedFields.length === 0;

  function updateValue(key: string, nextValue: unknown) {
    setValues((current) => ({ ...current, [key]: nextValue }));
    setSaveState("idle");
    setSaveMessage("");
    setEditedFields((current) => new Set(current).add(key));
    setReviewedFields((current) => {
      const next = new Set(current);
      next.delete(key);
      return next;
    });
  }

  function toggleReviewed(key: string, checked: boolean) {
    setReviewedFields((current) => {
      const next = new Set(current);
      if (checked) next.add(key);
      else next.delete(key);
      return next;
    });
  }

  async function persistDraft() {
    const assumptionsPatch = Object.fromEntries(
      [...editedFields].map((field) => [field, values[field]]),
    );
    const saved = await updateValuationDraft(
      draftId,
      assumptionsPatch,
      [...reviewedFields],
      updatedAt,
    );
    setUpdatedAt(saved.updated_at);
    setSourceMetadata(saved.source_metadata_json);
    setProvenance(saved.provenance_json);
    setWarnings(saved.warnings_json);
    return saved;
  }

  async function saveDraft() {
    setSaveState("saving");
    setSaveMessage("");
    try {
      await persistDraft();
      setSaveState("saved");
      setSaveMessage("Draft saved");
    } catch (error) {
      setSaveState("error");
      setSaveMessage(error instanceof Error ? error.message : "Save failed");
    }
  }

  async function refreshSources() {
    setSaveState("saving");
    setSaveMessage("");
    try {
      const saved = await persistDraft();
      await refreshValuationDraft(draftId, saved.updated_at);
      window.location.reload();
    } catch (error) {
      setSaveState("error");
      setSaveMessage(error instanceof Error ? error.message : "Refresh failed");
    }
  }

  async function resetField(key: string) {
    setSaveState("saving");
    setSaveMessage("");
    try {
      const saved = await persistDraft();
      await resetValuationDraftFields(draftId, [key], saved.updated_at);
      window.location.reload();
    } catch (error) {
      setSaveState("error");
      setSaveMessage(error instanceof Error ? error.message : "Reset failed");
    }
  }

  async function archiveDraft() {
    setSaveState("saving");
    setSaveMessage("");
    try {
      await archiveValuationDraft(draftId, updatedAt);
      window.location.assign(`/companies/${company.id}/valuation`);
    } catch (error) {
      setSaveState("error");
      setSaveMessage(error instanceof Error ? error.message : "Archive failed");
      setArchiveConfirmationOpen(false);
    }
  }

  function renderProvenance(key: string) {
    const rawEntry = provenance[key];
    const entry = provenanceEntry(rawEntry);
    const edited = editedFields.has(key);
    const source = edited ? "User edited" : provenanceLabel(rawEntry);
    const claimType = edited ? "User Assumption" : entry.claim_type || "Unclassified";
    const warning = typeof entry.warnings === "string" ? entry.warnings : null;
    const displayEntry = edited ? { ...entry, is_placeholder: false, requires_review: false } : entry;

    return (
      <div style={{ display: "grid", gap: "8px", marginTop: "10px" }}>
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
          <span className={sourceBadgeClass(displayEntry)}>
            <Database size={12} style={{ marginRight: "5px" }} />
            {displayEntry.is_placeholder ? "Placeholder" : source}
          </span>
          <span className="badge">{claimType}</span>
          {entry.confidence ? <span className="badge">{entry.confidence} confidence</span> : null}
        </div>
        {displayEntry.is_placeholder ? (
          <span style={{ color: "var(--warning)", fontSize: "12px" }}>{source}</span>
        ) : null}
        {warning ? (
          <span style={{ color: "var(--danger)", fontSize: "12px" }}>{warning}</span>
        ) : null}
        {edited ? (
          <button
            type="button"
            className="secondary-button"
            title={`Reset ${key} to the latest source value`}
            aria-label={`Reset ${key} to source`}
            onClick={() => resetField(key)}
            disabled={saveState === "saving"}
            style={{ height: "40px", justifySelf: "start", padding: 0, width: "40px" }}
          >
            <RotateCcw size={15} />
          </button>
        ) : null}
      </div>
    );
  }

  function renderReviewControl(key: string) {
    if (!reviewFields.has(key)) return null;
    const valid = reviewFieldValueIsValid(key, values[key]);
    return (
      <label
        style={{
          alignItems: "center",
          display: "flex",
          gap: "8px",
          marginTop: "12px",
          textTransform: "none",
        }}
      >
        <input
          type="checkbox"
          name="reviewed_field"
          value={key}
          checked={reviewedFields.has(key)}
          disabled={!valid}
          onChange={(event) => toggleReviewed(key, event.target.checked)}
          style={{ margin: 0, width: "16px" }}
        />
        {valid ? "Reviewed for this valuation" : "Enter a valid value before review"}
      </label>
    );
  }

  return (
    <form action={action} style={{ display: "grid", gap: "20px" }}>
      {warnings.length > 0 ? (
        <section className="panel" style={{ borderLeft: "4px solid var(--warning)", padding: "20px" }}>
          <div style={{ alignItems: "center", display: "flex", gap: "8px" }}>
            <AlertTriangle size={18} color="var(--warning)" />
            <h2 style={{ fontSize: "18px", margin: 0 }}>Draft Warnings</h2>
          </div>
          <ul style={{ marginBottom: 0 }}>
            {warnings.map((warning) => <li key={warning}>{warning}</li>)}
          </ul>
        </section>
      ) : null}

      {sourceMetadata.reporting_currency ? (
        <section className="panel" style={{ padding: "16px 20px" }}>
          <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: "8px" }}>
            <strong>Reporting Currency</strong>
            <span className="badge">{sourceMetadata.reporting_currency}</span>
            <span className="badge">
              {(sourceMetadata.reporting_currency_source || "unknown").replaceAll("_", " ")}
            </span>
            <span className="badge">{sourceMetadata.reporting_currency_confidence || "unknown"} confidence</span>
          </div>
          {sourceMetadata.oldest_source_as_of || sourceMetadata.latest_source_as_of ? (
            <p className="subtitle" style={{ marginBottom: 0, marginTop: "10px" }}>
              Source dates: {sourceMetadata.oldest_source_as_of || "unknown"} to {sourceMetadata.latest_source_as_of || "unknown"}.
            </p>
          ) : null}
          {sourceMetadata.stale_source_fields?.length ? (
            <p style={{ color: "var(--warning)", marginBottom: 0, marginTop: "10px" }}>
              Stale fields requiring review: {sourceMetadata.stale_source_fields.join(", ")}.
            </p>
          ) : null}
          {sourceMetadata.freshness_unknown_fields?.length ? (
            <p style={{ color: "var(--warning)", marginBottom: 0, marginTop: "10px" }}>
              Fields with unknown freshness: {sourceMetadata.freshness_unknown_fields.join(", ")}.
            </p>
          ) : null}
        </section>
      ) : null}

      <section className="panel" style={{ padding: "20px" }}>
        <h2 style={{ fontSize: "18px", marginTop: 0 }}>Model Settings</h2>
        <div className="form-grid" style={{ padding: 0 }}>
          <div className="field">
            <label htmlFor="model-name">Model Name</label>
            <input
              id="model-name"
              name="name"
              defaultValue={`Reviewed Autofill DCF - ${new Date().toISOString().split("T")[0]}`}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="model-description">Description</label>
            <input id="model-description" name="description" defaultValue="Reviewed assumption draft" />
          </div>
          <div className="field">
            <label htmlFor="model-type">Model Type</label>
            <select id="model-type" name="model_type" defaultValue="fcff_dcf">
              <option value="fcff_dcf">Standard FCFF DCF</option>
              <option value="distressed">Distressed Company DCF</option>
              <option value="financial_services">Financial Services (Excess Return)</option>
            </select>
          </div>
        </div>
      </section>

      <input type="hidden" name="scenario" value="Base" />
      <input type="hidden" name="reinvestment_method" value="sales_to_capital" />
      <input type="hidden" name="draft_updated_at" value={updatedAt} />

      <section className="panel" style={{ padding: "20px" }}>
        <h2 style={{ fontSize: "18px", marginTop: 0 }}>Revenue Growth Path</h2>
        <div className="field">
          <label htmlFor="revenue-growth">Year-by-Year Growth (JSON)</label>
          <textarea
            id="revenue-growth"
            name="revenue_growth_years_json"
            rows={4}
            value={growthText}
            onChange={(event) => {
              const next = event.target.value;
              setGrowthText(next);
              try {
                updateValue("revenue_growth_years_json", JSON.parse(next));
              } catch {
                updateValue("revenue_growth_years_json", next);
              }
            }}
            required
          />
          {renderProvenance("revenue_growth_years_json")}
          {renderReviewControl("revenue_growth_years_json")}
        </div>
      </section>

      {FIELD_GROUPS.map((group) => (
        <section className="panel" style={{ padding: "20px" }} key={group.title}>
          <h2 style={{ fontSize: "18px", marginTop: 0 }}>{group.title}</h2>
          <div className="form-grid" style={{ padding: 0 }}>
            {group.fields.map((field) => (
              <div className="field" key={field.key} style={{ alignContent: "start" }}>
                <label htmlFor={field.key}>{field.label}</label>
                <input
                  id={field.key}
                  name={field.key}
                  type="number"
                  step="any"
                  value={typeof values[field.key] === "number" ? (values[field.key] as number) : ""}
                  onChange={(event) => updateValue(
                    field.key,
                    event.target.value === "" ? "" : Number(event.target.value),
                  )}
                  required
                />
                {renderProvenance(field.key)}
                {renderReviewControl(field.key)}
              </div>
            ))}
          </div>
        </section>
      ))}

      {Object.entries(draft.assumptions).map(([key, value]) => {
        if (RENDERED_FIELDS.has(key) || key === "scenario" || key === "reinvestment_method") return null;
        const serialized = typeof value === "object" && value !== null ? JSON.stringify(value) : String(value ?? "");
        return <input key={key} type="hidden" name={key} value={serialized} />;
      })}
      {[...editedFields].map((field) => (
        <input key={field} type="hidden" name="edited_field" value={field} />
      ))}

      <section
        className="panel"
        style={{
          alignItems: "center",
          display: "flex",
          justifyContent: "space-between",
          gap: "16px",
          padding: "20px",
          position: "sticky",
          bottom: "16px",
          zIndex: 5,
        }}
      >
        <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: "10px" }}>
          {promotionReady ? (
            <CheckCircle2 size={20} color="var(--success)" />
          ) : (
            <ShieldCheck size={20} color="var(--warning)" />
          )}
          <div>
            <strong>{promotionReady ? "Ready to create" : `${unresolvedFields.length} fields require review`}</strong>
            <div style={{ color: "var(--muted)", fontSize: "12px", marginTop: "3px" }}>
              {promotionReady
                ? `All required assumptions for ${company.ticker} have been reviewed.`
                : unresolvedFields.slice(0, 4).join(", ")}
            </div>
          </div>
        </div>
        <div style={{ alignItems: "center", display: "flex", gap: "10px" }}>
          <span style={{ color: saveState === "error" ? "var(--danger)" : "var(--muted)", fontSize: "12px" }}>
            {saveState === "saving" ? "Saving..." : saveMessage}
          </span>
          <button type="button" className="secondary-button" onClick={() => setArchiveConfirmationOpen(true)} disabled={saveState === "saving"}>
            <Archive size={15} />
            Archive
          </button>
          {archiveConfirmationOpen ? (
            <div role="alertdialog" aria-labelledby="archive-draft-title" style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
              <strong id="archive-draft-title">Archive this draft?</strong>
              <button type="button" className="secondary-button" onClick={archiveDraft} disabled={saveState === "saving"}>Confirm archive</button>
              <button type="button" className="secondary-button" onClick={() => setArchiveConfirmationOpen(false)} disabled={saveState === "saving"}>Cancel</button>
            </div>
          ) : null}
          <button type="button" className="secondary-button" onClick={saveDraft} disabled={saveState === "saving"}>
            Save Draft
          </button>
          <button type="button" className="secondary-button" onClick={refreshSources} disabled={saveState === "saving"}>
            Refresh Sources
          </button>
          <button type="submit" className="primary-button" disabled={!promotionReady}>
            Confirm and Create Model
          </button>
        </div>
      </section>
    </form>
  );
}
