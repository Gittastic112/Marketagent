import type { MarketPrice } from "./api.ts";

export type MarketPriceSourceTone = "default" | "success" | "warning";

export function marketPriceSource(price: MarketPrice): {
  label: string;
  tone: MarketPriceSourceTone;
} {
  switch (price.provider_name) {
    case "manual":
      return { label: "Manual entry", tone: "default" };
    case "legacy_unknown":
      return { label: "Legacy source", tone: "warning" };
    case "yfinance_personal":
      return { label: "yfinance (unofficial)", tone: "warning" };
    case "alpha_vantage":
      return { label: "Alpha Vantage", tone: "success" };
    case undefined:
      return { label: "Source unavailable", tone: "warning" };
    default:
      return { label: price.provider_name, tone: "success" };
  }
}

function readableValue(value: string): string {
  return value.replaceAll("_", " ");
}

export function marketPriceTiming(price: MarketPrice): string {
  const parts = [readableValue(price.price_type || "unknown timing")];
  if (price.delay_minutes !== null && price.delay_minutes !== undefined) {
    parts.push(`${price.delay_minutes} min delay`);
  }
  if (price.adjustment_state && price.adjustment_state !== "not_applicable") {
    parts.push(readableValue(price.adjustment_state));
  }
  return parts.join(" / ");
}
