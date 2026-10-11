"use client";

import { AlertTriangle, Archive, CheckCircle2, Database, RotateCcw, ShieldCheck } from "lucide-react";
import { ValuationSourceRefreshPanel } from "./source-refresh-panel";
import type { Company } from "@/lib/api";
import { provenanceLabel, reviewFieldValueIsValid } from "@/lib/autofill-review";
import type { useAutofillDraft } from "./use-autofill-draft";
import { FIELD_GROUPS, TEXT_FIELDS, RENDERED_FIELDS, provenanceEntry, sourceBadgeClass } from "./autofill-draft-fields";

export function AutofillDraftReviewView({ company, draft, action, values, reviewedFields, editedFields, sourceMetadata, provenance, warnings, saveState, saveMessage, pipelineBusy, setPipelineBusy, archiveConfirmationOpen, setArchiveConfirmationOpen, defaultsAccepted, updatedAt, growthText, setGrowthText, reviewFields, unresolvedFields, invalidDefaultFields, promotionReady, updateValue, acceptCurrentDefaults, toggleReviewed, persistDraft, saveDraft, loadRefreshedDraft, refreshSources, resetField, archiveDraft }: ReturnType<typeof useAutofillDraft>) {
  function renderProvenance(key: string) {
    const rawEntry = provenance[key];
    const entry = provenanceEntry(rawEntry);
    const edited = editedFields.has(key);
    const source = edited ? "User edited" : provenanceLabel(rawEntry);
    const claimType = edited ? "User Assumption" : entry.claim_type || "Unclassified";
    const warning = typeof entry.warnings === "string" ? entry.warnings : null;
    const sourceParts = [
      typeof entry.source_file === "string" ? entry.source_file : null,
      typeof entry.source_sheet === "string" ? entry.source_sheet : null,
      typeof entry.source_row === "string" ? `row ${entry.source_row}` : null,
      typeof entry.source_column === "string" ? entry.source_column : null,
    ].filter(Boolean);
    const sourceAsOf = typeof entry.source_as_of === "string" ? entry.source_as_of : null;
    const sourceUrl = typeof entry.source_url === "string" && /^https?:\/\//i.test(entry.source_url) ? entry.source_url : null;
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
        {sourceParts.length > 0 ? (
          <span style={{ color: "var(--muted)", fontSize: "12px" }}>
            {sourceParts.join(" · ")}{sourceAsOf ? ` · as of ${sourceAsOf}` : ""}
          </span>
        ) : null}
        {sourceAsOf && sourceParts.length === 0 ? <small>As of {sourceAsOf}{entry.is_stale ? " · stale, review required" : ""}</small> : null}
        {sourceUrl ? <a href={sourceUrl} target="_blank" rel="noreferrer">Open source evidence</a> : null}
        {typeof entry.unit === "string" ? <small>Source unit: {entry.unit}</small> : null}
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
      <ValuationSourceRefreshPanel companyId={company.id} beforeQueue={persistDraft}
        onFinished={loadRefreshedDraft} onBusyChange={setPipelineBusy} />
      <fieldset disabled={pipelineBusy} className="valuation-draft-fields">
        {warnings.length > 0 ? (
          <details className="panel valuation-draft-warnings">
            <summary>
              <AlertTriangle size={18} color="var(--warning)" />
              <span><strong>{warnings.length} draft warnings</strong> <small>Review details</small></span>
            </summary>
            <ul>
              {warnings.map((warning) => <li key={warning}>{warning}</li>)}
            </ul>
          </details>
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

        {sourceMetadata.input_readiness_summary ? (
          <section className="panel" style={{ padding: "16px 20px" }}>
            <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: "8px" }}>
              <strong>Valuation Input Readiness</strong>
              <span className="badge">{sourceMetadata.input_readiness_summary.field_count} tracked inputs</span>
              <span className="badge badge-danger">
                {sourceMetadata.input_readiness_summary.required_missing_fields.length} required missing
              </span>
              <span className="badge badge-warn">
                {sourceMetadata.input_readiness_summary.required_review_fields.length} required to review
              </span>
            </div>
            <p className="subtitle" style={{ marginBottom: 0, marginTop: "10px" }}>
              Optional and model-specific inputs stay visible below. Missing values are not replaced with industry aggregate cash flows.
            </p>
          </section>
        ) : null}

        <section className="panel valuation-default-confirmation">
          <div>
            <h2>Use all current defaults</h2>
            <p>
              Create the model from the values already shown below. You can still edit and rerun it later.
            </p>
          </div>
          <label className="valuation-default-checkbox">
            <input
              type="checkbox"
              checked={defaultsAccepted}
              disabled={reviewFields.size === 0 || invalidDefaultFields.length > 0}
              onChange={(event) => acceptCurrentDefaults(event.target.checked)}
            />
            <span>I understand these values are estimates and accept all current valid defaults.</span>
          </label>
          {reviewFields.size === 0 ? (
            <p className="valuation-default-note">No additional default confirmation is required for this draft.</p>
          ) : invalidDefaultFields.length > 0 ? (
            <p className="inline-error">
              Defaults cannot be accepted yet. Fix invalid values for: {invalidDefaultFields.join(", ")}.
            </p>
          ) : (
            <p className="valuation-default-note">
              One check confirms {reviewFields.size} default assumption{reviewFields.size === 1 ? "" : "s"}.
            </p>
          )}
        </section>

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

        <details className="panel valuation-draft-group">
          <summary>
            <span>Currency and Narrative Inputs</span>
            <small>Currency consistency and source-backed valuation story</small>
          </summary>
          <div className="form-grid valuation-draft-group-content">
            {TEXT_FIELDS.map((field) => (
              <div className="field" key={field.key} style={{ alignContent: "start" }}>
                <label htmlFor={field.key}>{field.label}</label>
                <textarea
                  id={field.key}
                  name={field.key}
                  rows={field.key.includes("story") || field.key.includes("note") ? 3 : 1}
                  value={typeof values[field.key] === "string" ? values[field.key] as string : ""}
                  onChange={(event) => updateValue(field.key, event.target.value)}
                  required={field.required}
                />
                {renderProvenance(field.key)}
                {renderReviewControl(field.key)}
              </div>
            ))}
          </div>
        </details>

        <details className="panel valuation-draft-group">
          <summary>
            <span>Revenue Growth Path</span>
            <small>Year-by-year growth assumptions</small>
          </summary>
          <div className="field valuation-draft-group-content">
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
        </details>

        {FIELD_GROUPS.map((group) => (
          <details className="panel valuation-draft-group" key={group.title}>
            <summary>
              <span>{group.title}</span>
              <small>{group.fields.length} assumptions</small>
            </summary>
            <div className="form-grid valuation-draft-group-content">
              {group.fields.map((field) => (
                <div className="field" key={field.key} style={{ alignContent: "start" }}>
                  <label htmlFor={field.key}>{field.label}</label>
                  <input
                    id={field.key}
                    name={field.formName || field.key}
                    type="number"
                    step="any"
                    value={typeof values[field.key] === "number" ? (values[field.key] as number) : ""}
                    onChange={(event) => updateValue(
                      field.key,
                      event.target.value === "" ? "" : Number(event.target.value),
                    )}
                    required={field.required !== false}
                  />
                  {renderProvenance(field.key)}
                  {renderReviewControl(field.key)}
                </div>
              ))}
            </div>
          </details>
        ))}

        {Object.entries(draft.assumptions).map(([key, value]) => {
          if (RENDERED_FIELDS.has(key) || key === "scenario" || key === "reinvestment_method") return null;
          const serialized = typeof value === "object" && value !== null ? JSON.stringify(value) : String(value ?? "");
          return <input key={key} type="hidden" name={key} value={serialized} />;
        })}
        {[...editedFields].map((field) => (
          <input key={field} type="hidden" name="edited_field" value={field} />
        ))}

        <section className="panel valuation-draft-actions">
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
          <div className="valuation-draft-action-buttons">
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
              Refresh Stored Inputs
            </button>
            <button type="submit" className="primary-button" disabled={!promotionReady}>
              Confirm and Create Model
            </button>
          </div>
        </section>
      </fieldset>
    </form>
  );
}
