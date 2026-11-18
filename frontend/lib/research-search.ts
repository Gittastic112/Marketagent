import type { Company } from "./api/companies.ts";

/** Only internal research destinations from the authorized search endpoint are navigable. */
export function researchResultHref(value: string): string | null {
  if (!value.startsWith("/") || value.startsWith("//") || /[\u0000-\u0020\u007f\\]/.test(value)) return null;
  try {
    const url = new URL(value, "https://marketagent.invalid");
    if (url.origin !== "https://marketagent.invalid" || !/^\/(companies|documents|raw-documents|events|alerts|thesis-notes|decisions|research|ai-outputs|narratives)(\/|$)/.test(url.pathname)) return null;
    return `${url.pathname}${url.search}${url.hash}`;
  } catch { return null; }
}

export function matchingResearchCompanies(companies: readonly Company[], query: string, market: string): Company[] {
  const normalized = query.trim().toLocaleLowerCase();
  return companies.filter(company => (!market || company.market === market) && (!normalized ||
    [company.name, company.ticker, company.local_symbol, company.primary_exchange, company.isin, ...(company.aliases_json ?? [])]
      .join(" ").toLocaleLowerCase().includes(normalized)))
    .sort((a, b) => Number(b.ticker.toLocaleLowerCase() === normalized) - Number(a.ticker.toLocaleLowerCase() === normalized)
      || a.ticker.localeCompare(b.ticker) || a.id - b.id);
}
