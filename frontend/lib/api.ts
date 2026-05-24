const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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

export type RawDocument = {
  id: number;
  company_id: number | null;
  source_id: number;
  document_type: string;
  title: string;
  url: string | null;
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

export async function fetchApi<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}
