/** Public-source queue. Provider calls run in the local worker, not a page request. */
import { fetchApi, postApi } from "./transport.ts";

export type ValuationRefreshRun = {
  id: number;
  company_id: number | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  scheduled_for: string | null;
  steps: Array<{ name: string; status: string; company_id?: number; run_id?: number; warnings?: string[] }>;
  warnings: string[];
  draft_ids: number[];
};

export type ValuationRefreshStatus = {
  enabled: boolean;
  timezone: string;
  local_time: string;
  next_scheduled_at: string | null;
  latest_run: ValuationRefreshRun | null;
  policy: string;
  runtime_requirement: string;
};

export function fetchValuationRefreshStatus(companyId: number) {
  return fetchApi<ValuationRefreshStatus>(`/companies/${companyId}/valuation-source-refresh`);
}

export function queueValuationSourceRefresh(companyId: number) {
  return postApi<ValuationRefreshRun>(`/companies/${companyId}/valuation-source-refresh`, {});
}

export function fetchValuationRefreshRun(runId: number) {
  return fetchApi<ValuationRefreshRun>(`/valuation-source-refresh/${runId}`);
}

export function cancelValuationSourceRefresh(runId: number) {
  return postApi<ValuationRefreshRun>(`/valuation-source-refresh/${runId}/cancel`, {});
}
