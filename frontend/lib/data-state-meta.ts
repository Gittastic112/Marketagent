import type { ApiMeta } from "./api";

export type DataStateTone = "success" | "warning" | "danger" | "muted";

export type DataStateBadge = {
  label: string;
  tone: DataStateTone;
};

export type ApiMetaSummary = {
  allStale: boolean;
  someStale: boolean;
  allUnavailable: boolean;
  someUnavailable: boolean;
  hasMock: boolean;
  hasManual: boolean;
  warnings: string[];
};

function sentenceCase(value: string) {
  if (!value) {
    return value;
  }
  return `${value.charAt(0).toUpperCase()}${value.slice(1).toLowerCase()}`;
}

export function buildDataStateBadges(meta: (ApiMeta & { is_mock?: boolean }) | null | undefined): DataStateBadge[] {
  if (!meta) {
    return [];
  }

  const badges: DataStateBadge[] = [];

  if (meta.status !== "success") {
    badges.push({ label: sentenceCase(meta.status), tone: "danger" });
  } else if (meta.is_stale) {
    badges.push({ label: "Stale", tone: "warning" });
  } else {
    badges.push({ label: "Live", tone: "success" });
  }

  if (meta.is_mock || meta.source === "mock") {
    badges.push({ label: "Mock Data", tone: "warning" });
  } else if (meta.source === "manual" || (meta as any).is_manual) {
    badges.push({ label: "Manual Data", tone: "warning" });
  }

  if (meta.confidence && meta.confidence !== "high") {
    badges.push({ label: `${sentenceCase(meta.confidence)} confidence`, tone: "muted" });
  }

  if (meta.processing_time_ms !== null && meta.processing_time_ms !== undefined) {
    badges.push({ label: `${meta.processing_time_ms}ms`, tone: "muted" });
  }

  return badges;
}

export function summarizeApiMetas(
  metas: Array<(ApiMeta & { is_mock?: boolean }) | null | undefined>
): ApiMetaSummary {
  const presentMetas = metas.filter((meta): meta is ApiMeta & { is_mock?: boolean } => Boolean(meta));

  if (presentMetas.length === 0) {
    return {
      allStale: false,
      someStale: false,
      allUnavailable: false,
      someUnavailable: false,
      hasMock: false,
      hasManual: false,
      warnings: []
    };
  }

  const successfulMetas = presentMetas.filter((meta) => meta.status === "success");
  const unavailableMetas = presentMetas.filter((meta) => meta.status !== "success");

  return {
    allStale: successfulMetas.length === presentMetas.length && successfulMetas.every((meta) => meta.is_stale),
    someStale: successfulMetas.some((meta) => meta.is_stale),
    allUnavailable: unavailableMetas.length === presentMetas.length,
    someUnavailable: unavailableMetas.length > 0,
    hasMock: presentMetas.some((meta) => Boolean(meta.is_mock) || meta.source === "mock"),
    hasManual: presentMetas.some((meta) => meta.source === "manual" || (meta as any).is_manual),
    warnings: Array.from(new Set(presentMetas.flatMap((meta) => meta.warnings || [])))
  };
}

export function extractWarnings(
  metas: Array<(ApiMeta & { is_mock?: boolean }) | null | undefined>
): string[] {
  const presentMetas = metas.filter((meta): meta is ApiMeta & { is_mock?: boolean } => Boolean(meta));
  return Array.from(new Set(presentMetas.flatMap((meta) => meta.warnings || [])));
}
