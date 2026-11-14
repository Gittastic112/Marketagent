import { fetchApi } from "./transport.ts";

export type ReviewQueue = {
  captured_at: string; portfolio_id: number | null;
  items: { identity: string; domain: string; record_id: number; company_id: number | null; ticker: string | null;
    title: string; reason: string; state: string; relevant_at: string; href: string; action: string;
    permission_scope: "owned" | "shared_source"; severity_basis: string }[];
  counts: Record<string, number>; total: number; returned: number; limit: number; truncated: boolean;
  basis: string; limitations: string[];
};
export const getReviewQueue = () => fetchApi<ReviewQueue>("/review-queue");
