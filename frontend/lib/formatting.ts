export function formatCurrency(value: number | null | undefined, currencyCode: string = "USD", maximumFractionDigits: number = 2): string {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits,
  }).format(value);
}

export function formatPercent(value: number | null | undefined, maximumFractionDigits: number = 2): string {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits,
  }).format(value);
}

export function formatNumber(value: number | null | undefined, maximumFractionDigits: number = 2): string {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits,
  }).format(value);
}

const dataLabels: Record<string, string> = {
  sec: "SEC",
  sec_filing: "SEC filing",
  sec_filing_metadata: "SEC filing metadata",
  xbrl_facts: "XBRL facts",
  yfinance_personal: "yfinance (personal use)",
  reviewed_candidate_unit: "Reviewed source unit",
  needs_follow_up: "Needs follow-up",
};

/** Display stored codes without changing their values or implying stronger evidence. */
export function formatDataLabel(value: string | null | undefined): string {
  if (!value) return "Not available";
  return dataLabels[value] ?? value.replaceAll("_", " ").replace(/^./, first => first.toUpperCase());
}
