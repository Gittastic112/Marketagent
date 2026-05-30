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

function optionalStringList(formData: FormData, key: string): string[] | null {
  const value = optionalString(formData, key);
  if (value === null) {
    return null;
  }
  const items = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return items.length > 0 ? items : null;
}

export function buildCompanyPayload(formData: FormData): JsonPayload {
  return {
    ticker: requiredString(formData, "ticker").toUpperCase(),
    name: requiredString(formData, "name"),
    sector: optionalString(formData, "sector"),
    industry: optionalString(formData, "industry"),
    exchange: optionalString(formData, "exchange"),
    cik: optionalString(formData, "cik"),
    aliases_json: optionalStringList(formData, "aliases"),
    country: optionalString(formData, "country"),
    region: optionalString(formData, "region"),
    currency: optionalString(formData, "currency")?.toUpperCase() ?? null,
    asset_type: optionalString(formData, "asset_type"),
    security_type: optionalString(formData, "security_type"),
    market_cap_category: optionalString(formData, "market_cap_category"),
    is_etf: formData.get("is_etf") === "on",
    etf_provider: optionalString(formData, "etf_provider"),
    active: formData.get("active") === "on"
  };
}

export function getRequiredFormId(formData: FormData, fieldName: string = "id"): string {
  const value = formData.get(fieldName);
  if (!value || typeof value !== "string" || !value.trim()) {
    throw new Error(`Missing required form field: ${fieldName}`);
  }
  return value.trim();
}

export function buildSourcePayload(formData: FormData): JsonPayload {
  return {
    name: requiredString(formData, "name"),
    source_type: requiredString(formData, "source_type"),
    base_url: optionalString(formData, "base_url"),
    reliability_score: optionalNumber(formData, "reliability_score"),
    active: formData.get("active") === "on"
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
    rss_xml: optionalString(formData, "rss_xml"),
    feed_url: optionalString(formData, "feed_url")
  };
}

export function buildSecFilingIngestionPayload(formData: FormData): JsonPayload {
  const filingsJson = optionalString(formData, "filings_json");
  const formType = optionalString(formData, "form_type");
  const filingYear = optionalNumber(formData, "filing_year");
  return {
    source_id: requiredNumber(formData, "source_id"),
    company_id: requiredNumber(formData, "company_id"),
    filings: filingsJson ? JSON.parse(filingsJson) : [],
    form_types: formType ? [formType] : ["10-K", "10-Q", "8-K"],
    filing_year: filingYear,
    limit: optionalNumber(formData, "limit") ?? 40,
    download_text: formData.get("download_text") === "on"
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

export function buildAlertReviewPayload(formData: FormData): JsonPayload {
  return {
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

export function buildPortfolioPayload(formData: FormData): JsonPayload {
  return {
    name: requiredString(formData, "name"),
    base_currency: requiredString(formData, "base_currency").toUpperCase(),
    description: optionalString(formData, "description")
  };
}

export function buildPortfolioHoldingPayload(formData: FormData): JsonPayload {
  return {
    portfolio_id: requiredNumber(formData, "portfolio_id"),
    company_id: optionalNumber(formData, "company_id"),
    ticker: requiredString(formData, "ticker").toUpperCase(),
    quantity: requiredNumber(formData, "quantity"),
    average_cost: requiredNumber(formData, "average_cost"),
    currency: requiredString(formData, "currency").toUpperCase(),
    as_of_date: requiredString(formData, "as_of_date")
  };
}

export function buildPortfolioTransactionPayload(formData: FormData): JsonPayload {
  return {
    portfolio_id: requiredNumber(formData, "portfolio_id"),
    company_id: optionalNumber(formData, "company_id"),
    ticker: requiredString(formData, "ticker").toUpperCase(),
    transaction_type: requiredString(formData, "transaction_type"),
    quantity: requiredNumber(formData, "quantity"),
    price: requiredNumber(formData, "price"),
    fees: requiredNumber(formData, "fees"),
    currency: requiredString(formData, "currency").toUpperCase(),
    transaction_date: requiredString(formData, "transaction_date"),
    notes: optionalString(formData, "notes")
  };
}

export function buildPortfolioCashBalancePayload(formData: FormData): JsonPayload {
  return {
    portfolio_id: requiredNumber(formData, "portfolio_id"),
    currency: requiredString(formData, "currency").toUpperCase(),
    amount: requiredNumber(formData, "amount"),
    as_of_date: requiredString(formData, "as_of_date")
  };
}

export function buildPortfolioSnapshotPayload(formData: FormData): JsonPayload {
  let payloadJson = null;
  const rawPayload = optionalString(formData, "payload_json");
  if (rawPayload) {
    try {
      payloadJson = JSON.parse(rawPayload);
    } catch {
      payloadJson = {};
    }
  }

  return {
    portfolio_id: requiredNumber(formData, "portfolio_id"),
    snapshot_date: requiredString(formData, "snapshot_date"),
    total_market_value: optionalNumber(formData, "total_market_value"),
    total_cost_basis: optionalNumber(formData, "total_cost_basis"),
    total_cash: optionalNumber(formData, "total_cash"),
    payload_json: payloadJson
  };
}

export function buildMarketPricePayload(formData: FormData): JsonPayload {
  return {
    company_id: optionalNumber(formData, "company_id"),
    ticker: requiredString(formData, "ticker").toUpperCase(),
    price: requiredNumber(formData, "price"),
    currency: requiredString(formData, "currency").toUpperCase(),
    as_of_date: requiredString(formData, "as_of_date")
  };
}

export function buildFinancialStatementPeriodPayload(formData: FormData): JsonPayload {
  return {
    company_id: optionalNumber(formData, "company_id"),
    period_type: requiredString(formData, "period_type"),
    year: requiredNumber(formData, "year"),
    quarter: optionalNumber(formData, "quarter"),
    report_date: requiredString(formData, "report_date"),
    currency: requiredString(formData, "currency").toUpperCase()
  };
}

export function buildFinancialMetricPayload(formData: FormData): JsonPayload {
  return {
    period_id: optionalNumber(formData, "period_id"),
    metric_name: requiredString(formData, "metric_name"),
    value: requiredNumber(formData, "value"),
    unit: optionalString(formData, "unit")
  };
}

export function buildValuationModelPayload(formData: FormData): JsonPayload {
  return {
    company_id: optionalNumber(formData, "company_id"),
    name: requiredString(formData, "name"),
    description: optionalString(formData, "description")
  };
}

export function buildDcfAssumptionSetPayload(formData: FormData): JsonPayload {
  const assumptionsJson = optionalString(formData, "assumptions_json");
  return {
    valuation_model_id: optionalNumber(formData, "valuation_model_id"),
    scenario: requiredString(formData, "scenario"),
    discount_rate: requiredNumber(formData, "discount_rate"),
    terminal_growth_rate: requiredNumber(formData, "terminal_growth_rate"),
    projection_years: requiredNumber(formData, "projection_years"),
    assumptions_json: assumptionsJson ? JSON.parse(assumptionsJson) : {}
  };
}

export function buildSocialPostPayload(formData: FormData): JsonPayload {
  return {
    platform: requiredString(formData, "platform"),
    source_url: requiredString(formData, "source_url"),
    author: optionalString(formData, "author"),
    raw_text: requiredString(formData, "raw_text"),
    published_at: optionalString(formData, "published_at")
  };
}

export function buildSentimentScorePayload(formData: FormData): JsonPayload {
  return {
    post_id: optionalNumber(formData, "post_id"),
    company_id: optionalNumber(formData, "company_id"),
    score: requiredString(formData, "score"),
    rationale: optionalString(formData, "rationale")
  };
}

export function buildNarrativeClusterPayload(formData: FormData): JsonPayload {
  return {
    name: requiredString(formData, "name"),
    description: optionalString(formData, "description")
  };
}

export function buildNarrativeClaimPayload(formData: FormData): JsonPayload {
  return {
    cluster_id: requiredNumber(formData, "cluster_id"),
    claim_text: requiredString(formData, "claim_text")
  };
}

export function buildNarrativeMentionPayload(formData: FormData): JsonPayload {
  return {
    cluster_id: requiredNumber(formData, "cluster_id"),
    post_id: requiredNumber(formData, "post_id"),
    context_text: optionalString(formData, "context_text")
  };
}

export function buildThesisAssumptionPayload(formData: FormData): JsonPayload {
  return {
    thesis_note_id: requiredNumber(formData, "thesis_note_id"),
    description: requiredString(formData, "description"),
    original_confidence: optionalString(formData, "original_confidence") ?? "medium",
    current_confidence: optionalString(formData, "current_confidence") ?? "medium"
  };
}

export function buildThesisChangePayload(formData: FormData): JsonPayload {
  return {
    thesis_note_id: requiredNumber(formData, "thesis_note_id"),
    change_summary: requiredString(formData, "change_summary"),
    drift_score: optionalNumber(formData, "drift_score") ?? 0
  };
}
