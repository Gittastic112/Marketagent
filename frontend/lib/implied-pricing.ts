import type { ImpliedPricingBasis } from "./api.ts";

// Display only the reconciled backend basis. Never recover legacy scalar ratios.
export function pricingRows(basis: ImpliedPricingBasis | null | undefined, blocked: boolean) {
  if (basis?.version !== 1) return [];
  return basis.methods.map((method) => {
    const reason = blocked || basis.isStale
      ? "Saved inputs or DCF diagnostics require review before using this ratio."
      : method.reason;
    const usable = !reason && typeof method.value === "number" && Number.isFinite(method.value);
    return { ...method, reason, display: usable ? `${method.value!.toFixed(1)}x` : "Not available" };
  });
}
