"use server";

import { revalidatePath } from "next/cache";
import { serverDeleteApi, serverPatchApi, serverPostApi } from "@/lib/server-api";
import { buildPortfolioHoldingPayload, buildPortfolioPayload, buildPortfolioTransactionPayload, buildPortfolioCashBalancePayload, buildPortfolioSnapshotPayload, buildMarketPricePayload, getRequiredFormId } from "@/lib/form-payloads";
import { actionFormString, createRecord, deleteRecord, updateRecord, formActionError } from "./shared";
import type { FormActionState } from "./shared";

export async function createPortfolio(formData: FormData) {
  await createRecord("/portfolios", buildPortfolioPayload(formData), ["/portfolio"]);
}

export async function updatePortfolio(formData: FormData) {
  await updateRecord("/portfolios", formData, buildPortfolioPayload(formData), ["/portfolio"]);
}

export async function createPortfolioHolding(formData: FormData) {
  await createRecord("/portfolio-holdings", buildPortfolioHoldingPayload(formData), ["/portfolio"]);
}

export async function updatePortfolioHolding(formData: FormData) {
  await updateRecord("/portfolio-holdings", formData, buildPortfolioHoldingPayload(formData), ["/portfolio"]);
}

export async function createPortfolioTransaction(formData: FormData) {
  await createRecord("/portfolio-transactions", buildPortfolioTransactionPayload(formData), ["/portfolio"]);
}

export async function updatePortfolioTransaction(formData: FormData) {
  await updateRecord("/portfolio-transactions", formData, buildPortfolioTransactionPayload(formData), ["/portfolio"]);
}

export async function createPortfolioCashBalance(formData: FormData) {
  await createRecord("/portfolio-cash-balances", buildPortfolioCashBalancePayload(formData), ["/portfolio"]);
}

export async function updatePortfolioCashBalance(formData: FormData) {
  await updateRecord("/portfolio-cash-balances", formData, buildPortfolioCashBalancePayload(formData), ["/portfolio"]);
}

export async function createPortfolioSnapshot(formData: FormData) {
  await createRecord("/portfolio-snapshots", buildPortfolioSnapshotPayload(formData), ["/portfolio"]);
}

export async function updatePortfolioSnapshot(formData: FormData) {
  await updateRecord("/portfolio-snapshots", formData, buildPortfolioSnapshotPayload(formData), ["/portfolio"]);
}

export async function createPortfolioBenchmark(formData: FormData) {
  const portfolioId = getRequiredFormId(formData, "portfolio_id");
  await serverPostApi("/portfolio-benchmarks", {
    portfolio_id: portfolioId,
    ticker: actionFormString(formData, "ticker"),
    currency: actionFormString(formData, "currency"),
    provider_name: actionFormString(formData, "provider_name") || "manual",
    provider_symbol: actionFormString(formData, "provider_symbol") || null,
    effective_from: actionFormString(formData, "effective_from"),
    active: true,
    notes: actionFormString(formData, "notes") || null,
  });
  revalidatePath(`/portfolio/${portfolioId}`);
}

export async function updatePortfolioBenchmark(formData: FormData) {
  const benchmarkId = getRequiredFormId(formData);
  const portfolioId = getRequiredFormId(formData, "portfolio_id");
  await serverPatchApi(`/portfolio-benchmarks/${benchmarkId}`, {
    ticker: actionFormString(formData, "ticker"),
    currency: actionFormString(formData, "currency"),
    provider_name: actionFormString(formData, "provider_name") || "manual",
    provider_symbol: actionFormString(formData, "provider_symbol") || null,
    effective_from: actionFormString(formData, "effective_from"),
    active: formData.get("active") === "on",
    notes: actionFormString(formData, "notes") || null,
  });
  revalidatePath(`/portfolio/${portfolioId}`);
}

export async function deletePortfolioBenchmark(formData: FormData) {
  const benchmarkId = getRequiredFormId(formData);
  const portfolioId = getRequiredFormId(formData, "portfolio_id");
  await serverDeleteApi(`/portfolio-benchmarks/${benchmarkId}`);
  revalidatePath(`/portfolio/${portfolioId}`);
}

export async function capturePortfolioSnapshot(formData: FormData) {
  const portfolioId = getRequiredFormId(formData, "portfolio_id");
  const asOfDate = actionFormString(formData, "as_of_date");
  await serverPostApi(
    `/portfolios/${portfolioId}/snapshots/capture?as_of_date=${encodeURIComponent(asOfDate)}`,
    {},
  );
  revalidatePath(`/portfolio/${portfolioId}`);
}

export async function createFxRateObservation(formData: FormData) {
  const portfolioId = getRequiredFormId(formData, "portfolio_id");
  await serverPostApi("/fx-rates", {
    base_currency: actionFormString(formData, "base_currency"),
    quote_currency: actionFormString(formData, "quote_currency"),
    rate: Number(actionFormString(formData, "rate")),
    as_of_date: actionFormString(formData, "as_of_date"),
    provider_name: actionFormString(formData, "provider_name") || "manual",
    source_url: actionFormString(formData, "source_url") || null,
  });
  revalidatePath(`/portfolio/${portfolioId}`);
}

export async function deleteFxRateObservation(formData: FormData) {
  const observationId = getRequiredFormId(formData);
  const portfolioId = getRequiredFormId(formData, "portfolio_id");
  await serverDeleteApi(`/fx-rates/${observationId}`);
  revalidatePath(`/portfolio/${portfolioId}`);
}

export async function deletePortfolioCashBalance(formData: FormData) {
  await deleteRecord("/portfolio-cash-balances", formData, ["/portfolio"]);
}

export async function deletePortfolioCashBalanceWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deletePortfolioCashBalance(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deletePortfolioSnapshot(formData: FormData) {
  await deleteRecord("/portfolio-snapshots", formData, ["/portfolio"]);
}

export async function deletePortfolioSnapshotWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deletePortfolioSnapshot(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deletePortfolio(formData: FormData) {
  await deleteRecord("/portfolios", formData, ["/portfolio"]);
}

export async function deletePortfolioWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deletePortfolio(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deletePortfolioHolding(formData: FormData) {
  await deleteRecord("/portfolio-holdings", formData, ["/portfolio"]);
}

export async function deletePortfolioHoldingWithState(
  _state: FormActionState,
  formData: FormData
): Promise<FormActionState> {
  try {
    await deletePortfolioHolding(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deletePortfolioTransaction(formData: FormData) {
  await deleteRecord("/portfolio-transactions", formData, ["/portfolio"]);
}

export async function deletePortfolioTransactionWithState(
  _state: FormActionState,
  formData: FormData
): Promise<FormActionState> {
  try {
    await deletePortfolioTransaction(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createMarketPrice(formData: FormData) {
  await createRecord("/market-prices", buildMarketPricePayload(formData), ["/market-prices", "/portfolio"]);
}

export async function updateMarketPrice(formData: FormData) {
  await updateRecord("/market-prices", formData, buildMarketPricePayload(formData), ["/market-prices", "/portfolio"]);
}

export async function deleteMarketPrice(formData: FormData) {
  await deleteRecord("/market-prices", formData, ["/market-prices", "/portfolio"]);
}

export async function deleteMarketPriceWithState(
  _state: FormActionState,
  formData: FormData
): Promise<FormActionState> {
  try {
    await deleteMarketPrice(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}
