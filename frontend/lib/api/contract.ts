/** Shared envelope and error identity. Safe for server and browser imports. */

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
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
