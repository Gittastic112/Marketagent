export type JsonPayload = Record<string, unknown>;

function formValue(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === "string" ? value.trim() : "";
}

function requiredString(formData: FormData, key: string): string {
  const value = formValue(formData, key);
  if (!value) {
    throw new Error(`${key} is required`);
  }
  return value;
}

function optionalString(formData: FormData, key: string): string | null {
  const value = formValue(formData, key);
  return value ? value : null;
}

function requiredNumber(formData: FormData, key: string): number {
  const value = requiredString(formData, key);
  return Number(value);
}

function optionalNumber(formData: FormData, key: string): number | null {
  const value = optionalString(formData, key);
  return value === null ? null : Number(value);
}

export function buildCompanyPayload(formData: FormData): JsonPayload {
  return {
    ticker: requiredString(formData, "ticker").toUpperCase(),
    name: requiredString(formData, "name"),
    sector: optionalString(formData, "sector"),
    industry: optionalString(formData, "industry"),
    exchange: optionalString(formData, "exchange"),
    cik: optionalString(formData, "cik"),
    active: formData.get("active") === "on"
  };
}

export function getRequiredFormId(formData: FormData): number {
  return requiredNumber(formData, "id");
}

export function buildSourcePayload(formData: FormData): JsonPayload {
  return {
    name: requiredString(formData, "name"),
    source_type: requiredString(formData, "source_type"),
    base_url: optionalString(formData, "base_url"),
    reliability_score: optionalNumber(formData, "reliability_score")
  };
}

export function buildRawDocumentPayload(formData: FormData): JsonPayload {
  return {
    company_id: optionalNumber(formData, "company_id"),
    source_id: requiredNumber(formData, "source_id"),
    document_type: requiredString(formData, "document_type"),
    title: requiredString(formData, "title"),
    url: optionalString(formData, "url"),
    raw_text: optionalString(formData, "raw_text"),
    content_hash: requiredString(formData, "content_hash")
  };
}

export function buildRssIngestionPayload(formData: FormData): JsonPayload {
  return {
    source_id: requiredNumber(formData, "source_id"),
    company_id: optionalNumber(formData, "company_id"),
    rss_xml: requiredString(formData, "rss_xml")
  };
}

export function buildSecFilingIngestionPayload(formData: FormData): JsonPayload {
  const filingsJson = requiredString(formData, "filings_json");
  return {
    source_id: requiredNumber(formData, "source_id"),
    company_id: requiredNumber(formData, "company_id"),
    filings: JSON.parse(filingsJson),
  };
}

export function buildEventPayload(formData: FormData): JsonPayload {
  return {
    company_id: optionalNumber(formData, "company_id"),
    raw_document_id: optionalNumber(formData, "raw_document_id"),
    event_type: requiredString(formData, "event_type"),
    information_speed: requiredString(formData, "information_speed"),
    title: requiredString(formData, "title"),
    description: optionalString(formData, "description"),
    credibility_score: optionalNumber(formData, "credibility_score"),
    novelty_score: optionalNumber(formData, "novelty_score"),
    impact_score: optionalNumber(formData, "impact_score"),
    priority_score: optionalNumber(formData, "priority_score")
  };
}

export function buildAlertPayload(formData: FormData): JsonPayload {
  return {
    event_id: optionalNumber(formData, "event_id"),
    company_id: optionalNumber(formData, "company_id"),
    alert_type: requiredString(formData, "alert_type"),
    severity: requiredString(formData, "severity"),
    title: requiredString(formData, "title"),
    summary: optionalString(formData, "summary"),
    why_it_matters: optionalString(formData, "why_it_matters"),
    what_changed: optionalString(formData, "what_changed"),
    evidence: optionalString(formData, "evidence"),
    confidence_bucket: requiredString(formData, "confidence_bucket"),
    review_status: requiredString(formData, "review_status"),
    review_notes: optionalString(formData, "review_notes")
  };
}

export function buildThesisNotePayload(formData: FormData): JsonPayload {
  return {
    company_id: requiredNumber(formData, "company_id"),
    title: requiredString(formData, "title"),
    thesis_text: requiredString(formData, "thesis_text"),
    status: requiredString(formData, "status")
  };
}
