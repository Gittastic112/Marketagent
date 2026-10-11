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
  const market = optionalString(formData, "market")?.toUpperCase() ?? null;
  const primaryExchange = optionalString(formData, "primary_exchange")?.toUpperCase() ?? null;
  const localSymbol = optionalString(formData, "local_symbol")?.toUpperCase() ?? null;
  return {
    market,
    primary_exchange: primaryExchange,
    local_symbol: localSymbol,
    ticker: requiredString(formData, "ticker").toUpperCase(),
    name: requiredString(formData, "name"),
    sector: optionalString(formData, "sector"),
    industry: optionalString(formData, "industry"),
    damodaran_industry: optionalString(formData, "damodaran_industry"),
    exchange: optionalString(formData, "exchange"),
    cik: optionalString(formData, "cik"),
    isin: optionalString(formData, "isin")?.toUpperCase() ?? null,
    regulatory_id: optionalString(formData, "regulatory_id")?.toUpperCase() ?? null,
    regulatory_id_type: optionalString(formData, "regulatory_id_type")?.toUpperCase() ?? null,
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

export function getRequiredFormId(formData: FormData, fieldName: string = "id"): number {
  const value = formData.get(fieldName);
  if (!value || typeof value !== "string" || !value.trim()) {
    throw new Error(`Missing required form field: ${fieldName}`);
  }
  const id = Number(value.trim());
  if (!Number.isInteger(id) || id <= 0) {
    throw new Error(`Invalid form field: ${fieldName}`);
  }
  return id;
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

export function buildRawDocumentMetadataPayload(formData: FormData): JsonPayload {
  return {
    company_id: optionalNumber(formData, "company_id"),
    source_id: requiredNumber(formData, "source_id"),
    document_type: requiredString(formData, "document_type"),
    title: requiredString(formData, "title"),
    url: optionalString(formData, "url"),
    published_at: optionalString(formData, "published_at"),
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
    source_id: optionalNumber(formData, "source_id"),
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
    description: optionalString(formData, "description"),
    model_type: optionalString(formData, "model_type")
  };
}

export function buildDcfAssumptionSetPayload(formData: FormData): JsonPayload {
  const revenueGrowthYearsStr = optionalString(formData, "revenue_growth_years_json");

  const payload: JsonPayload = {
    valuation_model_id: optionalNumber(formData, "valuation_model_id"),
    scenario: requiredString(formData, "scenario"),

    story_text: optionalString(formData, "story_text"),
    growth_story: optionalString(formData, "growth_story"),
    margin_story: optionalString(formData, "margin_story"),
    reinvestment_story: optionalString(formData, "reinvestment_story"),
    risk_story: optionalString(formData, "risk_story"),

    starting_revenue: optionalNumber(formData, "starting_revenue"),
    revenue_growth_years_json: revenueGrowthYearsStr ? JSON.parse(revenueGrowthYearsStr) : {},
    target_operating_margin: optionalNumber(formData, "target_operating_margin"),
    current_operating_margin: optionalNumber(formData, "current_operating_margin"),
    tax_rate: optionalNumber(formData, "tax_rate"),
    sales_to_capital_ratio: optionalNumber(formData, "sales_to_capital_ratio"),
    reinvestment_method: formData.get("reinvestment_method") as string || "sales_to_capital",
    starting_invested_capital: optionalNumber(formData, "starting_invested_capital"),

    risk_free_rate: optionalNumber(formData, "risk_free_rate"),
    equity_risk_premium: optionalNumber(formData, "equity_risk_premium"),
    beta: optionalNumber(formData, "beta"),
    cost_of_equity: optionalNumber(formData, "cost_of_equity"),
    pre_tax_cost_of_debt: optionalNumber(formData, "pre_tax_cost_of_debt"),
    debt_to_capital: optionalNumber(formData, "debt_to_capital"),
    equity_to_capital: optionalNumber(formData, "equity_to_capital"),
    wacc_start: optionalNumber(formData, "wacc_start"),
    wacc_terminal: optionalNumber(formData, "wacc_terminal"),

    terminal_growth_rate: optionalNumber(formData, "terminal_growth_rate"),
    terminal_roic: optionalNumber(formData, "terminal_roic"),

    cash: optionalNumber(formData, "cash"),
    cross_holdings: optionalNumber(formData, "cross_holdings"),
    minority_interests: optionalNumber(formData, "minority_interests"),
    preferred_stock: optionalNumber(formData, "preferred_stock"),
    debt: optionalNumber(formData, "debt"),
    operating_leases: optionalNumber(formData, "operating_leases"),
    employee_options_value: optionalNumber(formData, "employee_options_value"),
    diluted_shares: optionalNumber(formData, "diluted_shares"),
    basic_shares: optionalNumber(formData, "basic_shares"),
    current_market_price: optionalNumber(formData, "current_market_price"),
    cash_flow_currency: optionalString(formData, "cash_flow_currency")?.toUpperCase() || null,
    discount_rate_currency: optionalString(formData, "discount_rate_currency")?.toUpperCase() || null,
    currency_override_note: optionalString(formData, "currency_override_note"),
    projection_years_count: optionalNumber(formData, "projection_years") ?? 10,

    probability_of_failure: optionalNumber(formData, "probability_of_failure"),
    distress_sale_proceeds: optionalNumber(formData, "distress_sale_proceeds"),
    book_value_of_equity: optionalNumber(formData, "book_value_of_equity"),
    target_roe: optionalNumber(formData, "target_roe"),
    net_income: optionalNumber(formData, "net_income"),
    capex: optionalNumber(formData, "capex"),
    depreciation: optionalNumber(formData, "depreciation"),
    change_in_nwc: optionalNumber(formData, "change_in_nwc"),
    new_debt_issued: optionalNumber(formData, "new_debt_issued"),
    debt_repaid: optionalNumber(formData, "debt_repaid"),
    dividends: optionalNumber(formData, "dividends"),
    buybacks: optionalNumber(formData, "buybacks"),
    stock_issuances: optionalNumber(formData, "stock_issuances"),
    company_age: optionalNumber(formData, "company_age"),
  };
  for (const [field, value] of Object.entries(payload)) {
    if (typeof value === "number" && !Number.isFinite(value)) throw new Error(`${field} must be a finite number`);
  }
  if (formData.has("base_assumption_set_id")) {
    // Absent controls preserve the owned server-side basis. Blank controls clear it.
    for (const field of Object.keys(payload)) {
      const control = field === "projection_years_count" ? "projection_years" : field;
      if (!formData.has(control)) delete payload[field];
    }
    payload.base_assumption_set_id = getRequiredFormId(formData, "base_assumption_set_id");
    payload.base_assumption_set_updated_at = requiredString(formData, "base_assumption_set_updated_at");
  }
  return payload;
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
    event_id: requiredNumber(formData, "event_id"),
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
