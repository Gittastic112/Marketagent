export type CurrencyConsistencySeverity = "ok" | "warning" | "blocking";

export type CurrencyConsistencyCheck = {
  canSave: boolean;
  severity: CurrencyConsistencySeverity;
  message: string;
};

export type CurrencyConsistencyInput = {
  companyMarket?: string | null;
  companyCurrency?: string | null;
  cashFlowCurrency?: string | null;
  discountRateCurrency?: string | null;
  overrideNote?: string | null;
};

function normalizeCurrency(value: string | null | undefined) {
  return value?.trim().toUpperCase() || "";
}

export function buildCurrencyConsistencyCheck(input: CurrencyConsistencyInput): CurrencyConsistencyCheck {
  const companyMarket = input.companyMarket?.trim().toUpperCase() || "";
  const companyCurrency = normalizeCurrency(input.companyCurrency);
  const cashFlowCurrency = normalizeCurrency(input.cashFlowCurrency || companyCurrency);
  const discountRateCurrency = normalizeCurrency(input.discountRateCurrency || cashFlowCurrency);
  const overrideNote = input.overrideNote?.trim() || "";

  if (cashFlowCurrency && discountRateCurrency && cashFlowCurrency !== discountRateCurrency) {
    if (!overrideNote) {
      return {
        canSave: false,
        severity: "blocking",
        message: `Risk-free currency ${discountRateCurrency} differs from cash-flow currency ${cashFlowCurrency}. Add an explicit override note before saving.`,
      };
    }
    return {
      canSave: true,
      severity: "warning",
      message: `Risk-free currency ${discountRateCurrency} differs from cash-flow currency ${cashFlowCurrency}. Saving is allowed because an explicit override note was provided.`,
    };
  }

  if (companyMarket === "IN" && cashFlowCurrency === "USD") {
    return {
      canSave: true,
      severity: "warning",
      message: "India company valuation is using USD cash flows. Confirm this is intentional and source-backed.",
    };
  }

  return {
    canSave: true,
    severity: "ok",
    message: "Currencies are consistent.",
  };
}
