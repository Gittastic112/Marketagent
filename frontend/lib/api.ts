/** Compatibility entry point. New code should import the owning lib/api module. */
export { ApiError } from "./api/contract.ts";
export type { ApiMeta, ApiErrorDetail, ApiResponse } from "./api/contract.ts";
export * from "./api/companies.ts";
export * from "./api/valuation.ts";
export * from "./api/documents.ts";
export * from "./api/ai.ts";
export * from "./api/health.ts";
export * from "./api/evidence.ts";
export * from "./api/portfolio.ts";
export * from "./api/market.ts";
export * from "./api/daily-brief.ts";
export * from "./api/operations.ts";
export * from "./api/financials.ts";
export * from "./api/relative-valuation.ts";
export * from "./api/research.ts";
export * from "./api/macro.ts";
export * from "./api/real-options.ts";
export * from "./api/valuation-priors.ts";
export * from "./api/valuation-drafts.ts";
export {
  fetchApi,
  fetchApiResponse,
  postApi,
  postFormApi,
  postApiFormData,
  patchApi,
  putApi,
  deleteApi,
} from "./api/transport.ts";
export { default } from "./api/transport.ts";
