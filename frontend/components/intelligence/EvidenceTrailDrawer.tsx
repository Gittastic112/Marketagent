"use client";

import { ExternalLink, FileText, ShieldCheck, X } from "lucide-react";
import { useEffect, useState } from "react";

import {
  DataFreshnessIndicator,
  ErrorState,
  LoadingState,
  PartialDataNotice,
} from "@/components/ui/data-states";
import {
  fetchApiResponse,
  type ApiErrorDetail,
  type ApiMeta,
  type EvidenceTrail,
} from "@/lib/api";

type EvidenceTrailDrawerProps = {
  alertId?: number;
  eventId?: number;
  isOpen: boolean;
  onClose: () => void;
};

function formatTimestamp(value: string | null | undefined) {
  return value ? new Date(value).toLocaleString() : "Timestamp unavailable";
}

function sectionLabel(origin: EvidenceTrail["excerpt_origin"]) {
  if (origin === "event.evidence_reference") return "Exact source passage";
  if (origin === "alert.evidence") return "Alert evidence";
  if (origin === "event.description") return "Event description";
  if (origin === "alert.summary") return "Alert summary";
  return "No claim context";
}

export function EvidenceTrailDrawer({
  alertId,
  eventId,
  isOpen,
  onClose,
}: EvidenceTrailDrawerProps) {
  const [trail, setTrail] = useState<EvidenceTrail | null>(null);
  const [meta, setMeta] = useState<ApiMeta | undefined>();
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<ApiErrorDetail[]>([]);

  useEffect(() => {
    if (!isOpen) return;

    const path = alertId
      ? `/alerts/${alertId}/evidence-trail`
      : eventId
        ? `/events/${eventId}/evidence-trail`
        : null;
    if (!path) {
      setErrors([{ code: "MISSING_EVIDENCE_TARGET", message: "No alert or event was selected." }]);
      setTrail(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setErrors([]);
    setTrail(null);
    void fetchApiResponse<EvidenceTrail>(path)
      .then((response) => {
        if (cancelled) return;
        setMeta(response.meta);
        setErrors(response.errors);
        setTrail(response.data);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const message = error instanceof Error ? error.message : "Unknown request failure";
        setErrors([{ code: "FETCH_ERROR", message }]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [alertId, eventId, isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      <button
        aria-label="Close evidence trail"
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(15, 23, 42, 0.34)",
          border: 0,
          zIndex: 99,
          cursor: "default",
        }}
        type="button"
      />
      <aside
        aria-labelledby="evidence-trail-title"
        aria-modal="true"
        role="dialog"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "560px",
          maxWidth: "94vw",
          backgroundColor: "var(--surface)",
          borderLeft: "1px solid var(--border)",
          boxShadow: "-4px 0 24px rgba(0,0,0,0.16)",
          zIndex: 100,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <header
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <div>
            <h2 id="evidence-trail-title" style={{ margin: 0, fontSize: "1.15rem" }}>
              Evidence Trail
            </h2>
            {meta ? (
              <div style={{ marginTop: "6px" }}>
                <DataFreshnessIndicator meta={meta} />
              </div>
            ) : null}
          </div>
          <button
            aria-label="Close"
            className="btn btn-outline"
            onClick={onClose}
            style={{ width: "36px", height: "36px", padding: 0, display: "grid", placeItems: "center" }}
            title="Close"
            type="button"
          >
            <X aria-hidden="true" size={18} />
          </button>
        </header>

        <div style={{ flex: 1, overflowY: "auto", padding: "20px" }}>
          {loading ? <LoadingState message="Fetching evidence trail..." /> : null}
          {!loading && errors.length > 0 ? (
            <ErrorState message="Could not fetch the evidence trail" errors={errors} />
          ) : null}

          {!loading && trail ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              {trail.evidence_status !== "complete" ? (
                <PartialDataNotice
                  message={
                    trail.evidence_status === "missing"
                      ? "No complete source chain is stored for this claim."
                      : "The claim is only partially traceable to a stored source."
                  }
                />
              ) : null}

              <section>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "10px" }}>
                  <span className="badge badge-outline">{trail.claim_type}</span>
                  <span className="badge badge-outline">{trail.confidence} confidence</span>
                  <span className="badge badge-outline">{trail.evidence_status} evidence</span>
                  {trail.locator.precision !== "none" ? (
                    <span className="badge badge-outline">{trail.locator.precision}-level locator</span>
                  ) : null}
                </div>
                <h3 style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0 0 8px" }}>
                  {sectionLabel(trail.excerpt_origin)}
                </h3>
                <blockquote
                  style={{
                    margin: 0,
                    padding: "12px 14px",
                    borderLeft: "3px solid var(--accent)",
                    background: "var(--bg)",
                    color: "var(--text)",
                    fontSize: "0.9rem",
                    lineHeight: 1.55,
                  }}
                >
                  {trail.claim_excerpt ?? "No supporting claim context is stored."}
                </blockquote>
                {trail.locator.reference_id ? (
                  <p style={{ margin: "8px 0 0", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                    {trail.locator.label}
                    {trail.locator.start_char !== null && trail.locator.end_char !== null
                      ? ` | characters ${trail.locator.start_char}-${trail.locator.end_char}`
                      : ""}
                    {trail.locator.confidence_label ? ` | ${trail.locator.confidence_label} confidence` : ""}
                  </p>
                ) : null}
              </section>

              {trail.alert ? (
                <section>
                  <h3 style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0 0 8px" }}>
                    Alert
                  </h3>
                  <div style={{ borderTop: "1px solid var(--border)", paddingTop: "10px" }}>
                    <strong>{trail.alert.title}</strong>
                    {trail.alert.why_it_matters ? (
                      <p style={{ margin: "6px 0 0", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                        {trail.alert.why_it_matters}
                      </p>
                    ) : null}
                  </div>
                </section>
              ) : null}

              {trail.event ? (
                <section>
                  <h3 style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0 0 8px" }}>
                    Triggering Event
                  </h3>
                  <div style={{ borderTop: "1px solid var(--border)", paddingTop: "10px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                      <strong>{trail.event.title}</strong>
                      <span className="badge badge-outline">{trail.event.event_type}</span>
                    </div>
                    {trail.event.description ? (
                      <p style={{ margin: "6px 0 0", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                        {trail.event.description}
                      </p>
                    ) : null}
                    <p style={{ margin: "8px 0 0", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                      Event time: {formatTimestamp(trail.event.event_time ?? trail.event.created_at)}
                    </p>
                  </div>
                </section>
              ) : null}

              {trail.document || trail.source ? (
                <section>
                  <h3 style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0 0 8px" }}>
                    Source Record
                  </h3>
                  <div style={{ borderTop: "1px solid var(--border)", paddingTop: "10px" }}>
                    {trail.source ? (
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                        <ShieldCheck aria-hidden="true" size={16} />
                        <strong>{trail.source.name}</strong>
                        <span className="badge badge-outline">{trail.source.source_type}</span>
                        {trail.source.reliability_score !== null ? (
                          <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                            Reliability {trail.source.reliability_score}/100
                          </span>
                        ) : null}
                      </div>
                    ) : null}
                    {trail.document ? (
                      <>
                        <div style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
                          <FileText aria-hidden="true" size={16} style={{ marginTop: "2px", flex: "0 0 auto" }} />
                          <div>
                            <strong>{trail.document.title}</strong>
                            <p style={{ margin: "4px 0 0", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                              {trail.document.document_type} | Published {formatTimestamp(trail.document.published_at)}
                            </p>
                          </div>
                        </div>
                        <div className="button-row" style={{ marginTop: "12px", flexWrap: "wrap" }}>
                          {trail.locator.internal_href ? (
                            <a className="secondary-button" href={trail.locator.internal_href}>
                              {trail.locator.precision === "region" || trail.locator.precision === "span"
                                ? "Open exact evidence"
                                : "Review source context"}
                            </a>
                          ) : null}
                          {trail.locator.asset_href ? (
                            <a className="secondary-button" href={trail.locator.asset_href} target="_blank" rel="noopener noreferrer">
                              Open stored PDF
                              <ExternalLink aria-hidden="true" size={14} />
                            </a>
                          ) : null}
                          {trail.locator.source_href ? (
                            <a className="secondary-button" href={trail.locator.source_href} target="_blank" rel="noopener noreferrer">
                              Open original
                              <ExternalLink aria-hidden="true" size={14} />
                            </a>
                          ) : null}
                        </div>
                      </>
                    ) : null}
                  </div>
                </section>
              ) : null}

              {trail.thesis_impacts.length > 0 ? (
                <section>
                  <h3 style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0 0 8px" }}>
                    Thesis Impact
                  </h3>
                  <div style={{ display: "grid", gap: "8px" }}>
                    {trail.thesis_impacts.map((impact) => (
                      <div key={impact.id} style={{ borderTop: "1px solid var(--border)", paddingTop: "10px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                          <strong>{impact.assumption_description}</strong>
                          <span className="badge badge-outline">{impact.impact_classification}</span>
                        </div>
                        <p style={{ margin: "5px 0 0", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                          {impact.rationale}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              ) : null}

              {trail.valuation_impacts.length > 0 ? (
                <section>
                  <h3 style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0 0 8px" }}>
                    Valuation Impact
                  </h3>
                  <div style={{ display: "grid", gap: "8px" }}>
                    {trail.valuation_impacts.map((impact) => (
                      <div key={impact.id} style={{ borderTop: "1px solid var(--border)", paddingTop: "10px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                          <strong>{impact.parameter_name}</strong>
                          <span className="badge badge-outline">{impact.is_applied ? "applied" : "proposed"}</span>
                        </div>
                        <p style={{ margin: "5px 0 0", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                          {impact.old_value ?? "Unavailable"} to {impact.new_value ?? "Unavailable"}
                        </p>
                        {impact.rationale ? (
                          <p style={{ margin: "5px 0 0", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                            {impact.rationale}
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </section>
              ) : null}

              {trail.warnings.length > 0 ? (
                <section>
                  <h3 style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0 0 8px" }}>
                    Limitations
                  </h3>
                  <ul style={{ margin: 0, paddingLeft: "20px", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    {trail.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </section>
              ) : null}
            </div>
          ) : null}
        </div>
      </aside>
    </>
  );
}
