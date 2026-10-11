"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Clock3, RefreshCw } from "lucide-react";
import { fetchValuationRefreshRun, fetchValuationRefreshStatus, queueValuationSourceRefresh,
  type ValuationRefreshRun } from "@/lib/api/valuation-refresh";
import { useLatestResource } from "@/lib/use-latest-resource";

export function ValuationSourceRefreshPanel({ companyId, beforeQueue, onFinished, onBusyChange }: {
  companyId: number;
  beforeQueue: () => Promise<unknown>;
  onFinished: () => Promise<void>;
  onBusyChange: (busy: boolean) => void;
}) {
  const resource = useLatestResource(useCallback(() => fetchValuationRefreshStatus(companyId), [companyId]));
  const [run, setRun] = useState<ValuationRefreshRun | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const alive = useRef(true);
  const resumedRunId = useRef<number | null>(null);
  const callbacks = useRef({ onFinished, onBusyChange });
  useEffect(() => { callbacks.current = { onFinished, onBusyChange }; }, [onFinished, onBusyChange]);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const pending = run?.status === "queued" || run?.status === "running";

  useEffect(() => {
    const existing = resource.data?.latest_run;
    if (run || !existing || resumedRunId.current === existing.id
      || !["queued", "running"].includes(existing.status)) return;
    // Resume observation after navigation, without submitting another job.
    // Do not repeatedly reattach a stale status snapshot after a polling error.
    resumedRunId.current = existing.id;
    setRun(existing);
    callbacks.current.onBusyChange(true);
  }, [resource.data, run]);

  useEffect(() => {
    if (!run || !pending) return;
    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const next = await fetchValuationRefreshRun(run.id);
        if (cancelled) return;
        if (!["queued", "running"].includes(next.status)) {
          await callbacks.current.onFinished();
          if (cancelled) return;
          callbacks.current.onBusyChange(false);
        }
        setRun(next);
      } catch (reason) {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : "Refresh status unavailable");
        setRun(null);
        callbacks.current.onBusyChange(false);
      }
    }, 3000);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [run, pending]);

  async function queue() {
    setStarting(true);
    setError(null);
    onBusyChange(true);
    try {
      await beforeQueue();
      const next = await queueValuationSourceRefresh(companyId);
      if (alive.current) {
        resumedRunId.current = next.id;
        setRun(next);
        if (!["queued", "running"].includes(next.status)) {
          await onFinished();
          if (alive.current) onBusyChange(false);
        }
      }
    } catch (reason) {
      if (alive.current) {
        setError(reason instanceof Error ? reason.message : "Could not queue source refresh");
        onBusyChange(false);
      }
    } finally {
      if (alive.current) setStarting(false);
    }
  }

  const status = resource.data;
  const displayedRun = run ?? status?.latest_run;
  const visibleSteps = displayedRun?.steps.filter(step => !step.company_id || step.company_id === companyId) ?? [];
  const visibleWarnings = [...new Set(displayedRun?.company_id === null && visibleSteps.length
    ? visibleSteps.flatMap(step => step.warnings ?? []) : displayedRun?.warnings ?? [])];
  const incomplete = displayedRun && !["success", "queued", "running"].includes(displayedRun.status);
  return (
    <section className="panel source-refresh-panel" aria-labelledby="source-refresh-title">
      <div className="section-header">
        <div>
          <h2 id="source-refresh-title">Refresh source inputs</h2>
          <p className="subtitle">Latest annual SEC statements, FRED rates and available prices feed this draft alongside your benchmark priors.</p>
        </div>
        <button type="button" className="secondary-button" onClick={queue} disabled={starting || pending}>
          <RefreshCw size={16} aria-hidden="true" />
          {starting ? "Saving draft..." : pending ? "Refreshing in background..." : "Fetch latest source inputs"}
        </button>
      </div>
      <p>Current edits are saved first. Suggestions require review; saved valuation models and financial approvals remain unchanged.</p>
      <p className="source-refresh-schedule muted"><Clock3 size={16} aria-hidden="true" /> <span>{resource.status === "loading" ? "Checking schedule..."
        : resource.status === "error" ? "Schedule status unavailable."
        : status?.enabled ? "Weekdays at 7:00 a.m. New York time. Computer and Docker must be running."
        : "Weekday automation is off. Manual refreshes require the local source-refresh worker."}</span></p>
      {pending ? <p role="status">{run?.status === "queued" ? "Queued. The local worker checks every 30 seconds."
        : `Running. ${run?.steps.length ?? 0} source steps recorded.`} Draft editing is paused until this refresh finishes.</p> : null}
      {error || resource.error ? <p role="alert" className="form-error">Status unavailable: {error || resource.error}. The job may still be running; reload to check before retrying.</p> : null}
      {displayedRun ? <details className="source-refresh-results" open={Boolean(incomplete)}>
        <summary>Last {displayedRun.company_id === null ? "scheduled batch" : "refresh"}: {displayedRun.status.replaceAll("_", " ")} · run #{displayedRun.id}</summary>
        <p className="muted"><time dateTime={displayedRun.finished_at ?? displayedRun.started_at}>{new Date(displayedRun.finished_at ?? displayedRun.started_at).toLocaleString()}</time>{displayedRun.company_id === null ? ". Showing this company and shared rate steps; batch status includes other companies." : ""}</p>
        <ul className="source-refresh-steps">{visibleSteps.map((step, index) => <li key={`${step.name}-${index}`}>
          <span>{step.name}</span>
          <span className="source-refresh-state" data-state={step.status}>{step.status.replaceAll("_", " ")}</span>
        </li>)}</ul>
        {visibleWarnings.length > 0 ? <ul className="source-refresh-warnings">{visibleWarnings.map(warning => <li key={warning}>{warning}</li>)}</ul> : null}
        <a href="/data-health">View processing history in Data Health</a>
      </details> : null}
      <div className="source-refresh-footer">
        <small>Forecast growth, margins, terminal assumptions and missing company-specific items still require analyst judgment. India statements use the existing upload/review workflow.</small>
        <a href={`/companies/${companyId}/fundamentals`}>Review extracted financial statements and source rows</a>
      </div>
    </section>
  );
}
