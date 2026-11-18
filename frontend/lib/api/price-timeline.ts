import { postApi } from "./transport.ts";

export type PriceSeries = {
  key: string; provider: string; symbol: string; currency: string;
  market: string | null; exchange: string | null; adjustment: string; claim_type: string;
};
export type PricePin = {
  id: number; company_id: number; thesis_note_id: number; text: string; created_at: string;
  anchor: PriceSeries & { price_id: number; date: string; price: string; observed_at: string; source_timestamp: string | null };
};
export type PricePoint = {
  date: string; price: number | null; price_id: number | null; fingerprint: string | null;
  change_pct: number | null; previous_date: string | null; large_move: boolean; gap_before: boolean;
  sources: { document_id: number; title: string; source: string; published: string; context_date: string; sample: boolean;
    event_id: number | null; summary: string | null }[];
  pins: PricePin[];
};
export type PriceTimeline = {
  series: PriceSeries | null; choices: PriceSeries[]; points: PricePoint[];
  move_threshold_pct: number; truncated: boolean; context_limited: boolean;
};
export function addPricePin(companyId: number, payload: {
  thesis_id: number; price_id: number; fingerprint: string; request_id: string; text: string;
}) {
  return postApi<PricePin>(`/companies/${companyId}/price-timeline/pins`, payload);
}
