import "server-only";

import type { ApiResponse } from "@/lib/api/contract";
import type { Portfolio, PortfolioValuation } from "@/lib/api/portfolio";
import { serverFetchApiResponse } from "@/lib/server-api";

// Both portfolio lists need current values. Bound each page's database pressure;
// one failed response retains its metadata without hiding the other portfolios.
export async function loadPortfolioValuations(portfolios: ReadonlyArray<Pick<Portfolio, "id">>) {
  const responses: ApiResponse<PortfolioValuation>[] = [];
  for (let offset = 0; offset < portfolios.length; offset += 4) {
    responses.push(...await Promise.all(portfolios.slice(offset, offset + 4).map(portfolio =>
      serverFetchApiResponse<PortfolioValuation>(`/portfolios/${portfolio.id}/valuation`))));
  }
  return responses;
}
