/** Price/FX evidence contracts. Preview and apply keep the original file bytes. */
import { postFormApi } from "./transport.ts";

export type EvidenceRowError = { row_index: number; field: string; message: string };
export type EvidencePreviewRow = {
  row_index: number;
  record_type: string | null;
  action: "create" | "skip" | "error";
  message: string;
  errors: EvidenceRowError[];
};
export type EvidencePreview = {
  is_preview: true;
  filename: string;
  content_sha256: string;
  byte_size: number;
  total_rows: number;
  create_count: number;
  skip_count: number;
  error_count: number;
  market_price_count: number;
  fx_rate_count: number;
  can_apply: boolean;
  claim_type: "Fact";
  contains_mock_data: false;
  scope: {
    portfolio_id: number;
    portfolio_name: string;
    holding_tickers: string[];
    benchmark_ticker: string | null;
    allowed_fx_pairs: string[];
  };
  rows: EvidencePreviewRow[];
};
export type EvidenceApplyResult = {
  status: "completed";
  processing_run_id: number;
  content_sha256: string;
  created_count: number;
  market_prices_created: number;
  fx_rates_created: number;
  skipped_duplicate_count: number;
  contains_mock_data: false;
  claim_type: "Fact";
};

export function previewPortfolioEvidence(portfolioId: number, file: File): Promise<EvidencePreview> {
  const data = new FormData();
  data.append("file", file);
  return postFormApi<EvidencePreview>(`/portfolios/${portfolioId}/evidence-bundle/preview`, data);
}

export function applyPortfolioEvidence(portfolioId: number, file: File, expectedSha256: string): Promise<EvidenceApplyResult> {
  const data = new FormData();
  data.append("file", file);
  data.append("expected_sha256", expectedSha256);
  return postFormApi<EvidenceApplyResult>(`/portfolios/${portfolioId}/evidence-bundle/apply`, data);
}
