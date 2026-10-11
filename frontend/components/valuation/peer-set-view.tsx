"use client";

import { readPeerCsvFile } from "@/lib/peer-csv-file";
import type { usePeerSetManager } from "./use-peer-set";
import { MULTIPLE_FIELDS, marketCapCoverageLabel, targetMarketCapCoverageLabel, DraftMember, DraftTarget, blankMember } from "./peer-set-fields";

export function PeerSetManagerView({ companyId, peerSets, defaultOpen, managerRef, name, setName, notes, setNotes, members, setMembers, targetEnabled, setTargetEnabled, target, setTarget, editing, history, warningAcknowledgements, setWarningAcknowledgements, csvText, setCsvText, csvPreview, setCsvPreview, csvLoading, setCsvLoading, csvSelection, busy, error, setError, message, setMessage, resetForm, updateMember, updateMultiple, saveSet, startEdit, reviewSet, archiveSet, restoreSet, toggleHistory, downloadTemplate, previewCsv, applyCsv, exportSet }: ReturnType<typeof usePeerSetManager>) {
  return (
    <details ref={managerRef} open={defaultOpen || undefined} style={{ marginBottom: "1rem", border: "1px solid var(--line)", borderRadius: "8px", padding: "0.75rem" }}>
      <summary style={{ cursor: "pointer", fontWeight: 650 }}>Manage reviewed peer sets</summary>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
        Enter sourced peer multiples only. Every mutation is version-checked and retained in history.
        Restored or edited sets return to Draft. Diagnostics flag stale, unaligned, sparse, or dispersed evidence without silently removing it.
      </p>

      {error && <div role="alert" className="error-box" style={{ marginBottom: "0.75rem" }}>{error}</div>}
      {message && <div className="success-box" style={{ marginBottom: "0.75rem" }}>{message}</div>}

      <fieldset style={{ border: "1px solid var(--line)", borderRadius: "8px", padding: "0.75rem", marginBottom: "1rem" }}>
        <legend>Source-preserving CSV import and export</legend>
        <p style={{ marginTop: 0, color: "var(--text-secondary)", fontSize: "0.82rem" }}>
          Preview never writes. Apply accepts only the exact SHA-256 previewed file and creates a Draft.
          Template v2 carries one identical sourced target-company profile across every peer row.
          Legacy member-only files remain accepted with a visible warning. Imported facts are
          user-supplied and are not independently verified.
        </p>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
          <button type="button" className="secondary-button" disabled={busy} onClick={downloadTemplate}>Download strict template</button>
          <label htmlFor={`peer-csv-${companyId}`} style={{ fontWeight: 600 }}>Peer CSV</label>
          <input
            id={`peer-csv-${companyId}`}
            type="file"
            accept=".csv,text/csv"
            disabled={busy || csvLoading}
            onChange={async (event) => {
              const file = event.target.files?.[0];
              const selection = ++csvSelection.current;
              setCsvText("");
              setCsvPreview(null);
              setError(null);
              setMessage(null);
              setCsvLoading(Boolean(file));
              if (!file) return;
              try {
                const text = await readPeerCsvFile(file);
                if (selection === csvSelection.current) setCsvText(text);
              } catch (caught) {
                if (selection === csvSelection.current) {
                  setError(caught instanceof Error ? caught.message : "Could not read the CSV file");
                }
              } finally {
                if (selection === csvSelection.current) setCsvLoading(false);
              }
            }}
          />
          <button type="button" className="secondary-button" disabled={busy || csvLoading || !csvText} onClick={previewCsv}>Preview CSV</button>
          <button type="button" className="btn btn-primary" disabled={busy || csvLoading || !csvPreview?.isValid} onClick={applyCsv}>Apply exact preview as Draft</button>
        </div>
        <p role="status" style={{ fontSize: "0.82rem" }}>
          {csvLoading ? "Reading CSV..." : "UTF-8 CSV only, up to 1 MB and 50 peer rows. Invalid files cannot be applied."}
        </p>
        {csvPreview && (
          <div style={{ marginTop: "0.6rem", fontSize: "0.82rem" }}>
            <strong>{csvPreview.isValid ? "Valid preview" : "Blocked preview"}</strong>: {csvPreview.memberCount} parsed peer(s), SHA-256 {csvPreview.sha256}.
            <div>
              Format v{csvPreview.formatVersion ?? "unknown"}
              {csvPreview.legacyFormat ? " (legacy member-only)" : ""} · target profile {csvPreview.targetContext ? "included" : "missing"}.
            </div>
            {csvPreview.errors.length > 0 && (
              <ul style={{ color: "#b42318", paddingLeft: "1.2rem" }}>
                {csvPreview.errors.map((item, index) => <li key={`${item.row}-${item.field}-${index}`}>Row {item.row ?? "file"}, {item.field}: {item.message}</li>)}
              </ul>
            )}
            <ul style={{ color: "#856404", paddingLeft: "1.2rem" }}>
              {csvPreview.warnings.map((warning) => <li key={warning}>{warning}</li>)}
            </ul>
          </div>
        )}
      </fieldset>

      {peerSets.length > 0 && (
        <div style={{ display: "grid", gap: "0.5rem", marginBottom: "1rem" }}>
          {peerSets.map((peerSet) => (
            <div key={peerSet.id} id={`peer-set-${peerSet.id}`} tabIndex={-1} style={{ border: "1px solid var(--line)", borderRadius: "6px", padding: "0.65rem" }}>
              <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
                <div style={{ flex: "1 1 220px" }}>
                  <strong>{peerSet.name}</strong>
                  <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                    v{peerSet.version} · {peerSet.includedMemberCount} included peers · {peerSet.aggregationMethod} · {peerSet.reviewStatus} · {peerSet.isActive ? "active" : "archived"}
                    {peerSet.reviewedAt ? ` · reviewed ${new Date(peerSet.reviewedAt).toLocaleDateString()}` : ""}
                  </div>
                  <div style={{ color: peerSet.diagnostics.warnings.length ? "#856404" : "var(--text-secondary)", fontSize: "0.8rem" }}>
                    {peerSet.diagnostics.warnings.length
                      ? `${peerSet.diagnostics.warnings.length} comparability warning(s)`
                      : "No threshold warnings; economic comparability still requires judgment."}
                  </div>
                  <div style={{ color: peerSet.reviewReceipt?.matchesCurrentDiagnostics ? "var(--text-secondary)" : "#856404", fontSize: "0.8rem" }}>
                    Diagnostic receipt: {peerSet.reviewReceipt?.matchesCurrentDiagnostics
                      ? `current as of ${peerSet.reviewReceipt.diagnosticsAsOf} (${peerSet.reviewReceipt.diagnosticsSha256.slice(0, 12)}…)`
                      : peerSet.reviewReceipt
                        ? "stale; current diagnostics must be re-acknowledged before valuation use"
                        : "not recorded; current diagnostics must be acknowledged before valuation use"}
                  </div>
                  {peerSet.storageConsistency.status !== "consistent" && (
                    <div style={{ color: "#b42318", fontSize: "0.8rem" }}>
                      Storage audit: {peerSet.storageConsistency.status}. Reload or repair before relying on this set.
                    </div>
                  )}
                  <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                    {peerSet.targetContext
                      ? `Target profile: ${peerSet.targetContext.sourceName} as of ${peerSet.targetContext.sourceAsOf}`
                      : "Target profile: not supplied; target-relative comparability is limited."}
                  </div>
                  <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                    {marketCapCoverageLabel(peerSet)}
                  </div>
                  {targetMarketCapCoverageLabel(peerSet) && (
                    <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                      {targetMarketCapCoverageLabel(peerSet)}
                    </div>
                  )}
                  {peerSet.targetStorageConsistency.status !== "consistent" && (
                    <div style={{ color: "#b42318", fontSize: "0.8rem" }}>
                      Target storage audit: {peerSet.targetStorageConsistency.status}. Repair before review or valuation use.
                    </div>
                  )}
                </div>
                {peerSet.isActive && (
                  <button className="secondary-button" type="button" disabled={busy} onClick={() => startEdit(peerSet.id)}>Edit</button>
                )}
                {peerSet.isActive && (peerSet.reviewStatus === "draft" || !peerSet.reviewReceipt?.matchesCurrentDiagnostics) && (
                  <button
                    className="secondary-button"
                    type="button"
                    disabled={busy || peerSet.storageConsistency.status === "mismatch" || peerSet.targetStorageConsistency.status === "mismatch" || (peerSet.diagnostics.warningCodes.length > 0 && !warningAcknowledgements[peerSet.id])}
                    onClick={() => reviewSet(peerSet)}
                  >
                    {peerSet.reviewStatus === "reviewed" ? "Re-acknowledge current diagnostics" : "Review and approve"}
                  </button>
                )}
                {peerSet.isActive ? (
                  <button className="secondary-button" type="button" disabled={busy} onClick={() => archiveSet(peerSet)}>Archive</button>
                ) : (
                  <button className="secondary-button" type="button" disabled={busy} onClick={() => restoreSet(peerSet)}>Restore as draft</button>
                )}
                <button className="secondary-button" type="button" disabled={busy} onClick={() => toggleHistory(peerSet.id)}>
                  {history[peerSet.id] ? "Hide history" : "Show history"}
                </button>
                <button className="secondary-button" type="button" disabled={busy} onClick={() => exportSet(peerSet.id)}>Export CSV</button>
              </div>
              {peerSet.diagnostics.warnings.length > 0 && (
                <>
                  <ul style={{ margin: "0.5rem 0 0", paddingLeft: "1.2rem", fontSize: "0.8rem", color: "#856404" }}>
                    {peerSet.diagnostics.warnings.map((warning, index) => (
                      <li key={`${warning.code}-${warning.method || "set"}-${index}`}>{warning.message}</li>
                    ))}
                  </ul>
                  {peerSet.isActive && (peerSet.reviewStatus === "draft" || !peerSet.reviewReceipt?.matchesCurrentDiagnostics) && (
                    <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginTop: "0.5rem", fontSize: "0.8rem" }}>
                      <input
                        type="checkbox"
                        checked={Boolean(warningAcknowledgements[peerSet.id])}
                        onChange={(event) => setWarningAcknowledgements((current) => ({
                          ...current,
                          [peerSet.id]: event.target.checked,
                        }))}
                      />
                      I reviewed the current diagnostic warning categories.
                    </label>
                  )}
                </>
              )}
              {history[peerSet.id] && (
                <ol style={{ margin: "0.65rem 0 0", paddingLeft: "1.4rem", fontSize: "0.8rem" }}>
                  {history[peerSet.id]?.map((revision) => (
                    <li key={revision.id}>
                      v{revision.version} {revision.action} · {revision.reviewStatus} · {revision.isActive ? "active" : "archived"} · target {revision.targetContext ? "sourced" : "missing"} · receipt {revision.reviewReceipt ? `${revision.reviewReceipt.diagnosticsAsOf} (${revision.reviewReceipt.diagnosticsSha256.slice(0, 12)}…)` : "none"} · changed {revision.changedFields.join(", ") || "none"} · {new Date(revision.createdAt).toLocaleString()}
                    </li>
                  ))}
                </ol>
              )}
            </div>
          ))}
        </div>
      )}

      <div style={{ display: "grid", gap: "0.75rem" }}>
        <h4 style={{ margin: 0 }}>{editing ? `Edit ${editing.name} (v${editing.version})` : "Create peer-set draft"}</h4>
        {editing?.reviewStatus === "reviewed" && (
          <p style={{ margin: 0, color: "#856404", fontSize: "0.85rem" }}>
            Saving changes will invalidate the current review. The prior reviewed revision remains in history.
          </p>
        )}
        <label>
          <span style={{ display: "block", fontWeight: 600, marginBottom: "0.25rem" }}>Peer-set name</span>
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Reviewed operating peers" style={{ width: "100%" }} />
        </label>
        <label>
          <span style={{ display: "block", fontWeight: 600, marginBottom: "0.25rem" }}>Selection notes</span>
          <textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Why these businesses are comparable" rows={2} style={{ width: "100%" }} />
        </label>

        <fieldset style={{ border: "1px solid var(--line)", borderRadius: "8px", padding: "0.75rem" }}>
          <legend>Sourced target-company comparability profile</legend>
          <label style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <input
              type="checkbox"
              checked={targetEnabled}
              onChange={(event) => setTargetEnabled(event.target.checked)}
            />
            Compare peers against sourced target facts
          </label>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
            Optional, but without it the app can only compare peers to each other. These facts are user-supplied and require review.
          </p>
          {targetEnabled && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "0.6rem" }}>
              <label>Target source name<input value={target.sourceName} onChange={(event) => setTarget((current) => ({ ...current, sourceName: event.target.value }))} /></label>
              <label>Target source URL<input type="url" value={target.sourceUrl} onChange={(event) => setTarget((current) => ({ ...current, sourceUrl: event.target.value }))} /></label>
              <label>Target source as of<input type="date" value={target.sourceAsOf} onChange={(event) => setTarget((current) => ({ ...current, sourceAsOf: event.target.value }))} /></label>
              <label>Target claim type
                <select value={target.claimType} onChange={(event) => setTarget((current) => ({ ...current, claimType: event.target.value as DraftTarget["claimType"] }))}>
                  <option value="Fact">Fact</option>
                  <option value="Source Summary">Source Summary</option>
                </select>
              </label>
              <label>Target country<input value={target.country} onChange={(event) => setTarget((current) => ({ ...current, country: event.target.value }))} /></label>
              <label>Target currency<input maxLength={3} value={target.currency} onChange={(event) => setTarget((current) => ({ ...current, currency: event.target.value.toUpperCase() }))} /></label>
              <label>Target fiscal period end<input type="date" value={target.fiscalPeriodEnd} onChange={(event) => setTarget((current) => ({ ...current, fiscalPeriodEnd: event.target.value }))} /></label>
              <label>Target accounting standard
                <select value={target.accountingStandard} onChange={(event) => setTarget((current) => ({ ...current, accountingStandard: event.target.value as DraftTarget["accountingStandard"] }))}>
                  <option value="">Not supplied</option>
                  <option value="IFRS">IFRS</option>
                  <option value="US GAAP">US GAAP</option>
                  <option value="IND AS">IND AS</option>
                  <option value="OTHER">Other</option>
                </select>
              </label>
              <label>Target market cap<input type="number" min="0.000001" step="any" value={target.marketCap} onChange={(event) => setTarget((current) => ({ ...current, marketCap: event.target.value }))} /></label>
              <label>Target revenue growth %<input type="number" min="-100" max="1000" step="any" value={target.revenueGrowthPct} onChange={(event) => setTarget((current) => ({ ...current, revenueGrowthPct: event.target.value }))} /></label>
              <label>Target EBITDA margin %<input type="number" min="-1000" max="100" step="any" value={target.ebitdaMarginPct} onChange={(event) => setTarget((current) => ({ ...current, ebitdaMarginPct: event.target.value }))} /></label>
              <label style={{ gridColumn: "1 / -1" }}>Target notes<input value={target.notes} onChange={(event) => setTarget((current) => ({ ...current, notes: event.target.value }))} /></label>
            </div>
          )}
        </fieldset>

        {members.map((member, index) => (
          <fieldset key={index} style={{ border: "1px solid var(--line)", borderRadius: "8px", padding: "0.75rem" }}>
            <legend>Peer {index + 1}</legend>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "0.6rem" }}>
              <label>Identifier<input value={member.identifier} onChange={(event) => updateMember(index, { identifier: event.target.value })} placeholder="TICKER" /></label>
              <label>Name<input value={member.name} onChange={(event) => updateMember(index, { name: event.target.value })} placeholder="Company name" /></label>
              <label>Source name<input value={member.sourceName} onChange={(event) => updateMember(index, { sourceName: event.target.value })} placeholder="Annual filing" /></label>
              <label>Source URL<input type="url" value={member.sourceUrl} onChange={(event) => updateMember(index, { sourceUrl: event.target.value })} placeholder="https://..." /></label>
              <label>Source as of<input type="date" value={member.sourceAsOf} onChange={(event) => updateMember(index, { sourceAsOf: event.target.value })} /></label>
              <label>Claim type
                <select value={member.claimType} onChange={(event) => updateMember(index, { claimType: event.target.value as DraftMember["claimType"] })}>
                  <option value="Fact">Fact</option>
                  <option value="Source Summary">Source Summary</option>
                </select>
              </label>
              <label>Country<input value={member.country} onChange={(event) => updateMember(index, { country: event.target.value })} placeholder="United States" /></label>
              <label>Currency<input value={member.currency} maxLength={3} onChange={(event) => updateMember(index, { currency: event.target.value.toUpperCase() })} placeholder="USD" /></label>
              <label>Fiscal period end<input type="date" value={member.fiscalPeriodEnd} onChange={(event) => updateMember(index, { fiscalPeriodEnd: event.target.value })} /></label>
              <label>Accounting standard
                <select value={member.accountingStandard} onChange={(event) => updateMember(index, { accountingStandard: event.target.value as DraftMember["accountingStandard"] })}>
                  <option value="">Not supplied</option>
                  <option value="IFRS">IFRS</option>
                  <option value="US GAAP">US GAAP</option>
                  <option value="IND AS">IND AS</option>
                  <option value="OTHER">Other</option>
                </select>
              </label>
              <label>Market cap<input type="number" min="0.000001" step="any" value={member.marketCap} onChange={(event) => updateMember(index, { marketCap: event.target.value })} /></label>
              <label>Revenue growth %<input type="number" min="-100" max="1000" step="any" value={member.revenueGrowthPct} onChange={(event) => updateMember(index, { revenueGrowthPct: event.target.value })} /></label>
              <label>EBITDA margin %<input type="number" min="-1000" max="100" step="any" value={member.ebitdaMarginPct} onChange={(event) => updateMember(index, { ebitdaMarginPct: event.target.value })} /></label>
              {MULTIPLE_FIELDS.map((field) => (
                <label key={field.id}>
                  {field.label}
                  <input type="number" min="0.000001" max="1000" step="any" value={member.multiples[field.id] || ""} onChange={(event) => updateMultiple(index, field.id, event.target.value)} />
                </label>
              ))}
              <label style={{ gridColumn: "1 / -1" }}>Peer notes<input value={member.notes} onChange={(event) => updateMember(index, { notes: event.target.value })} placeholder="Comparability caveat" /></label>
              <label style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <input type="checkbox" checked={member.included} onChange={(event) => updateMember(index, { included: event.target.checked })} />
                Include in aggregation
              </label>
            </div>
            {members.length > 1 && (
              <button type="button" className="secondary-button" style={{ marginTop: "0.6rem" }} onClick={() => setMembers((current) => current.filter((_, memberIndex) => memberIndex !== index))}>
                Remove peer
              </button>
            )}
          </fieldset>
        ))}

        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button type="button" className="secondary-button" onClick={() => setMembers((current) => [...current, blankMember()])} disabled={busy || members.length >= 50}>Add peer</button>
          <button type="button" className="btn btn-primary" onClick={saveSet} disabled={busy || !name.trim()}>
            {busy ? "Saving..." : editing ? "Save changes as new version" : "Save draft peer set"}
          </button>
          {editing && <button type="button" className="secondary-button" onClick={resetForm} disabled={busy}>Cancel edit</button>}
        </div>
      </div>
    </details>
  );
}
