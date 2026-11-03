import { PeerMultipleMethod, PeerTargetContext, PeerValuationMember, PeerValuationSet } from "@/lib/api";

export const MULTIPLE_FIELDS: Array<{ id: PeerMultipleMethod; label: string; }> = [
  { id: "pe", label: "P/E" },
  { id: "pbv", label: "P/B" },
  { id: "ps", label: "P/S" },
  { id: "ev_sales", label: "EV/Sales" },
  { id: "ev_ebitda", label: "EV/EBITDA" },
  { id: "ev_ebit", label: "EV/EBIT" },
];

export function marketCapCoverageLabel(peerSet: PeerValuationSet): string {
  const context = peerSet.diagnostics.comparabilityContext;
  const recordedCount = context.coverage.marketCap || 0;
  const groupedCount = Object.values(context.marketCapGroups).reduce(
    (total, group) => total + group.memberCount,
    0,
  );
  return `${groupedCount}/${recordedCount} peer market caps grouped by stated currency. No FX conversion is applied.`;
}

export function targetMarketCapCoverageLabel(peerSet: PeerValuationSet): string | null {
  const comparison = peerSet.diagnostics.comparabilityContext.targetComparisons.marketCap;
  if (!comparison) return null;
  const skippedCount = comparison.skippedMemberIdentifiers?.length || 0;
  return `Target size compared with ${comparison.comparedCount} ${comparison.currency || "same-currency"} peer(s); ${skippedCount} skipped.`;
}

export type DraftMember = {
  identifier: string;
  companyId?: number | null;
  name: string;
  included: boolean;
  sourceName: string;
  sourceUrl: string;
  sourceAsOf: string;
  claimType: "Fact" | "Source Summary";
  notes: string;
  country: string;
  currency: string;
  fiscalPeriodEnd: string;
  accountingStandard: "" | "IFRS" | "US GAAP" | "IND AS" | "OTHER";
  marketCap: string;
  revenueGrowthPct: string;
  ebitdaMarginPct: string;
  multiples: Partial<Record<PeerMultipleMethod, string>>;
};

export type DraftTarget = {
  sourceName: string;
  sourceUrl: string;
  sourceAsOf: string;
  claimType: "Fact" | "Source Summary";
  notes: string;
  country: string;
  currency: string;
  fiscalPeriodEnd: string;
  accountingStandard: "" | "IFRS" | "US GAAP" | "IND AS" | "OTHER";
  marketCap: string;
  revenueGrowthPct: string;
  ebitdaMarginPct: string;
};

export function blankTarget(): DraftTarget {
  return {
    sourceName: "",
    sourceUrl: "",
    sourceAsOf: "",
    claimType: "Fact",
    notes: "",
    country: "",
    currency: "",
    fiscalPeriodEnd: "",
    accountingStandard: "",
    marketCap: "",
    revenueGrowthPct: "",
    ebitdaMarginPct: "",
  };
}

export function fromTarget(target: PeerTargetContext): DraftTarget {
  return {
    sourceName: target.sourceName,
    sourceUrl: target.sourceUrl,
    sourceAsOf: target.sourceAsOf,
    claimType: target.claimType,
    notes: target.notes || "",
    country: target.country || "",
    currency: target.currency || "",
    fiscalPeriodEnd: target.fiscalPeriodEnd || "",
    accountingStandard: target.accountingStandard || "",
    marketCap: target.marketCap != null ? String(target.marketCap) : "",
    revenueGrowthPct: target.revenueGrowthPct != null ? String(target.revenueGrowthPct) : "",
    ebitdaMarginPct: target.ebitdaMarginPct != null ? String(target.ebitdaMarginPct) : "",
  };
}

export function targetPayload(target: DraftTarget): PeerTargetContext {
  return {
    sourceName: target.sourceName.trim(),
    sourceUrl: target.sourceUrl.trim(),
    sourceAsOf: target.sourceAsOf,
    claimType: target.claimType,
    notes: target.notes.trim() || undefined,
    country: target.country.trim() || undefined,
    currency: target.currency.trim().toUpperCase() || undefined,
    fiscalPeriodEnd: target.fiscalPeriodEnd || undefined,
    accountingStandard: target.accountingStandard || undefined,
    marketCap: target.marketCap.trim() ? Number(target.marketCap) : undefined,
    revenueGrowthPct: target.revenueGrowthPct.trim() ? Number(target.revenueGrowthPct) : undefined,
    ebitdaMarginPct: target.ebitdaMarginPct.trim() ? Number(target.ebitdaMarginPct) : undefined,
  };
}

export function blankMember(): DraftMember {
  return {
    identifier: "",
    name: "",
    included: true,
    sourceName: "",
    sourceUrl: "",
    sourceAsOf: "",
    claimType: "Fact",
    notes: "",
    country: "",
    currency: "",
    fiscalPeriodEnd: "",
    accountingStandard: "",
    marketCap: "",
    revenueGrowthPct: "",
    ebitdaMarginPct: "",
    multiples: {},
  };
}

export function fromMember(member: PeerValuationMember): DraftMember {
  return {
    identifier: member.identifier,
    companyId: member.companyId,
    name: member.name || "",
    included: member.included,
    sourceName: member.sourceName,
    sourceUrl: member.sourceUrl,
    sourceAsOf: member.sourceAsOf,
    claimType: member.claimType,
    notes: member.notes || "",
    country: member.country || "",
    currency: member.currency || "",
    fiscalPeriodEnd: member.fiscalPeriodEnd || "",
    accountingStandard: member.accountingStandard || "",
    marketCap: member.marketCap != null ? String(member.marketCap) : "",
    revenueGrowthPct: member.revenueGrowthPct != null ? String(member.revenueGrowthPct) : "",
    ebitdaMarginPct: member.ebitdaMarginPct != null ? String(member.ebitdaMarginPct) : "",
    multiples: Object.fromEntries(
      Object.entries(member.multiples).map(([method, value]) => [method, String(value)]),
    ),
  };
}

export function toPayload(member: DraftMember): PeerValuationMember {
  const multiples = Object.fromEntries(
    MULTIPLE_FIELDS.flatMap(({ id }) => {
      const raw = member.multiples[id]?.trim();
      return raw ? [[id, Number(raw)]] : [];
    }),
  );
  return {
    identifier: member.identifier.trim(),
    companyId: member.companyId,
    name: member.name.trim() || undefined,
    included: member.included,
    multiples,
    sourceName: member.sourceName.trim(),
    sourceUrl: member.sourceUrl.trim(),
    sourceAsOf: member.sourceAsOf,
    claimType: member.claimType,
    notes: member.notes.trim() || undefined,
    country: member.country.trim() || undefined,
    currency: member.currency.trim().toUpperCase() || undefined,
    fiscalPeriodEnd: member.fiscalPeriodEnd || undefined,
    accountingStandard: member.accountingStandard || undefined,
    marketCap: member.marketCap.trim() ? Number(member.marketCap) : undefined,
    revenueGrowthPct: member.revenueGrowthPct.trim() ? Number(member.revenueGrowthPct) : undefined,
    ebitdaMarginPct: member.ebitdaMarginPct.trim() ? Number(member.ebitdaMarginPct) : undefined,
  };
}

export function downloadCsv(filename: string, csvText: string) {
  const url = URL.createObjectURL(new Blob([csvText], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
