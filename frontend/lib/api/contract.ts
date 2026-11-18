/** Shared envelope and error identity. Safe for server and browser imports. */

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly processingRunId?: number;
  readonly retryable?: boolean;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    // Retain only safe public receipt fields, never rejected inputs or raw provider data.
    if (detail && typeof detail === "object") {
      if ("code" in detail && typeof detail.code === "string") this.code = detail.code;
      if ("processing_run_id" in detail && typeof detail.processing_run_id === "number"
        && Number.isSafeInteger(detail.processing_run_id) && detail.processing_run_id > 0) this.processingRunId = detail.processing_run_id;
      if ("retryable" in detail && typeof detail.retryable === "boolean") this.retryable = detail.retryable;
    }
  }
}

export type ApiMeta = {
  status: string;
  last_updated: string | null;
  source: string;
  is_stale: boolean;
  is_mock?: boolean;
  warnings: string[];
  confidence: string;
  processing_time_ms: number | null;
  request_id?: string | null;
};

export interface ApiErrorDetail {
  code: string;
  message: string;
  target?: string | null;
  retryable?: boolean;
  field?: string | null;
  provider?: string | null;
  processing_run_id?: number | null;
}

export interface ApiResponse<T> {
  data: T | null;
  meta: ApiMeta;
  errors: ApiErrorDetail[];
}

/** Transport failures are unavailable, never stale cached investment data. */
export function errorResponse<T>(code: string, message: string, status = "error"): ApiResponse<T> {
  return {
    data: null,
    meta: {
      status,
      last_updated: null,
      source: "transport",
      is_stale: false,
      warnings: [message],
      confidence: "none",
      processing_time_ms: null,
    },
    errors: [{ code, message }],
  };
}
