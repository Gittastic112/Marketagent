/** Contracts and endpoint helpers for documents. Import transport directly, never the compatibility facade. */
import { fetchApi, postApi } from "./transport.ts";
import type { FinancialExtractionCandidate } from "./financials.ts";
import type { SecFilingMetadata } from "./operations.ts";

export type RawDocument = {
  id: number;
  company_id: number | null;
  source_id: number;
  document_type: string;
  title: string;
  url: string | null;
  published_at?: string | null;
  raw_text?: string | null;
  raw_payload_json?: Record<string, unknown> | null;
  has_raw_text?: boolean;
  content_hash: string;
  ingested_at?: string;
  created_at?: string;
};

export type DocumentAsset = {
  id: number;
  raw_document_id: number;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  page_count: number;
  created_at: string;
};

export type PdfFinancialExtractionResult = {
  raw_document_id: number;
  asset: DocumentAsset;
  page_count: number;
  scanned_page_count: number;
  scanned_pages: number[];
  table_count: number;
  created_count: number;
  skipped_existing_count: number;
  warnings: string[];
  candidates: FinancialExtractionCandidate[];
};

export type FilingDiscovery = {
  company_id: number;
  market: string;
  provider_name: string;
  mode: "automated" | "manual";
  manual_required: boolean;
  filings: SecFilingMetadata[];
  next_action: string;
  official_manual_source?: {
    url: string;
    checked_on: string;
    security_isin: string;
    target_years: number[];
    required_documents: string[];
  } | null;
};

export type FilingSectionDiff = {
  id: number;
  current_section_id: number;
  prior_section_id: number | null;
  added_words: number;
  removed_words: number;
  diff_html: string | null;
  created_at: string;
};

export type FilingSection = {
  id: number;
  raw_document_id: number;
  item_name: string;
  title: string | null;
  text_content: string;
  word_count: number;
  created_at: string;
  updated_at: string;
  diffs_as_current: FilingSectionDiff[];
};

export async function listFilingSections(rawDocumentId: number): Promise<FilingSection[]> {
  return fetchApi<FilingSection[]>(`/raw-documents/${rawDocumentId}/sections`);
}

export async function parseFilingSections(rawDocumentId: number): Promise<{ status: string }> {
  return postApi<{ status: string }>(`/raw-documents/${rawDocumentId}/parse`, {});
}

export async function fetchRawDocumentSummaries(): Promise<RawDocument[]> {
  return fetchApi<RawDocument[]>("/raw-documents/summaries");
}
