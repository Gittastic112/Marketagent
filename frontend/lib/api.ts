const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const DEBUG_LOGS_ENABLED = process.env.NEXT_PUBLIC_DEBUG_LOGS !== "false";

function logApiStart(method: string, path: string) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} -> ${API_BASE_URL}${path}`);
  }
}

function logApiSuccess(method: string, path: string, status: number) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} succeeded with ${status}`);
  }
}

function logApiFailure(method: string, path: string, status: number) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} failed with ${status}`);
  }
}

export type Company = {
  id: number;
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  exchange: string | null;
  cik: string | null;
  active: boolean;
};

export type Source = {
  id: number;
  name: string;
  source_type: string;
  base_url: string | null;
  reliability_score: number | null;
};

export type RawDocument = {
  id: number;
  company_id: number | null;
  source_id: number;
  document_type: string;
  title: string;
  url: string | null;
  raw_text: string | null;
  content_hash: string;
};

export type EventRecord = {
  id: number;
  company_id: number | null;
  raw_document_id: number | null;
  event_type: string;
  information_speed: string;
  title: string;
  description: string | null;
  credibility_score: number | null;
  novelty_score: number | null;
  impact_score: number | null;
  priority_score: number | null;
};

export type AlertRecord = {
  id: number;
  event_id: number | null;
  company_id: number | null;
  alert_type: string;
  severity: string;
  title: string;
  summary: string | null;
  why_it_matters: string | null;
  confidence_bucket: string;
  review_status: string;
};

export type ThesisNote = {
  id: number;
  company_id: number;
  title: string;
  thesis_text: string;
  status: string;
};

export type DailyBrief = {
  title: string;
  date: string;
  summary: string;
  top_events: Array<{
    id: number;
    company: string | null;
    title: string;
    event_type: string;
    information_speed: string;
    description: string | null;
    credibility_score: number | null;
    novelty_score: number | null;
    impact_score: number | null;
    priority_score: number | null;
    source: string | null;
    source_url: string | null;
  }>;
  alerts: Array<{
    id: number;
    company: string | null;
    title: string;
    severity: string;
    confidence_bucket: string;
    review_status: string;
    summary: string | null;
  }>;
  follow_up_questions: string[];
};

export type SavedDailyBrief = {
  id: number;
  brief_date: string;
  title: string;
  summary: string;
  payload_json: DailyBrief;
  created_at: string;
};

export type RssIngestionResult = {
  created: number;
  skipped_duplicates: number;
};

export type SecFilingIngestionResult = {
  created: number;
  skipped_duplicates: number;
};

export type EventExtractionResult = {
  created: number;
  skipped_existing: number;
};

export async function fetchApi<T>(path: string): Promise<T> {
  logApiStart("GET", path);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    logApiFailure("GET", path, response.status);
    throw new Error(`API request failed: ${response.status}`);
  }

  logApiSuccess("GET", path, response.status);
  return response.json() as Promise<T>;
}

export async function postApi<T>(path: string, payload: unknown): Promise<T> {
  logApiStart("POST", path);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    logApiFailure("POST", path, response.status);
    throw new Error(`API request failed: ${response.status}`);
  }

  logApiSuccess("POST", path, response.status);
  return response.json() as Promise<T>;
}

export async function patchApi<T>(path: string, payload: unknown): Promise<T> {
  logApiStart("PATCH", path);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    logApiFailure("PATCH", path, response.status);
    throw new Error(`API request failed: ${response.status}`);
  }

  logApiSuccess("PATCH", path, response.status);
  return response.json() as Promise<T>;
}

export async function deleteApi(path: string): Promise<void> {
  logApiStart("DELETE", path);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    logApiFailure("DELETE", path, response.status);
    throw new Error(`API request failed: ${response.status}`);
  }

  logApiSuccess("DELETE", path, response.status);
}
