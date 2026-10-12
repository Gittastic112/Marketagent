import {
  createPortfolio,
  createPortfolioHolding,
  createPortfolioTransaction,
  deletePortfolioHoldingWithState,
  deletePortfolioTransactionWithState,
  deletePortfolioWithState,
  updatePortfolio,
  updatePortfolioHolding,
  updatePortfolioTransaction
} from "@/app/actions";
import Link from "next/link";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices, DataFreshnessIndicator } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import { loadPortfolioValuations } from "@/lib/server-portfolio";
import type { Company, Portfolio, PortfolioHolding, PortfolioTransaction } from "@/lib/api";
import { CsvImporter } from "@/components/csv-importer";

const securityTransactionTypes = [
  "buy",
  "sell",
  "dividend",
  "split",
  "bonus",
  "manual_adjustment"
];

const cashTransactionTypes = ["deposit", "withdrawal", "fee", "tax"];
const transactionTypes = [...securityTransactionTypes, ...cashTransactionTypes];

function transactionTypeLabel(transactionType: string): string {
  return transactionType
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function numberText(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 6 });
}

function companyLabel(companyId: number | null, companiesById: Map<number, Company>): string {
  if (companyId === null) {
    return "-";
  }
  return companiesById.get(companyId)?.ticker ?? `#${companyId}`;
}

function PortfolioSelect({
  portfolios,
  defaultValue,
  id
}: {
  portfolios: Portfolio[];
  defaultValue?: number;
  id: string;
}) {
  return (
    <SelectField defaultValue={defaultValue ?? ""} disabled={portfolios.length === 0} id={id} label="Portfolio" name="portfolio_id" required>
      <option value="">Select portfolio</option>
      {portfolios.map((portfolio) => (
        <option key={portfolio.id} value={portfolio.id}>
          {portfolio.name}
        </option>
      ))}
    </SelectField>
  );
}

function CompanySelect({
  companies,
  defaultValue,
  id
}: {
  companies: Company[];
  defaultValue?: number | null;
  id: string;
}) {
  return (
    <SelectField defaultValue={defaultValue ?? ""} id={id} label="Company" name="company_id">
      <option value="">Unlinked</option>
      {companies.map((company) => (
        <option key={company.id} value={company.id}>
          {company.ticker}
        </option>
      ))}
    </SelectField>
  );
}

export default async function PortfolioPage() {
  try {
    const [portfoliosRes, holdingsRes, transactionsRes, companiesRes] = await Promise.all([
      serverFetchApiResponse<Portfolio[]>("/portfolios"),
      serverFetchApiResponse<PortfolioHolding[]>("/portfolio-holdings"),
      serverFetchApiResponse<PortfolioTransaction[]>("/portfolio-transactions"),
      serverFetchApiResponse<Company[]>("/companies")
    ]);
    const portfolios = portfoliosRes.data || [];
    const holdings = holdingsRes.data || [];
    const transactions = transactionsRes.data || [];
    const companies = companiesRes.data || [];

    const today = new Date().toISOString().slice(0, 10);
    const portfoliosById = new Map(portfolios.map((portfolio) => [portfolio.id, portfolio]));
    const companiesById = new Map(companies.map((company) => [company.id, company]));

    const valuationsRes = await loadPortfolioValuations(portfolios);
    const valuations = valuationsRes.map(res => res.data);
    const valuationsById = new Map(
      valuations.filter(Boolean).map((v) => [v!.portfolio_id, v!])
    );

    const getHoldingValuation = (holdingId: number, portfolioId: number) => {
      const val = valuationsById.get(portfolioId);
      if (!val) return null;
      return val.holdings.find(h => h.holding_id === holdingId) || null;
    };

    const dataStateMetas = [
      portfoliosRes.meta,
      holdingsRes.meta,
      transactionsRes.meta,
      companiesRes.meta,
      ...valuationsRes.map((res) => res.meta)
    ];

    return (
      <>
        <div className="breadcrumb">
          <Link href="/portfolio">← Back to Portfolio Monitoring</Link>
        </div>
        <PageHeader eyebrow="Portfolio Management" title="Manage Data" status={`${portfolios.length} portfolios`} />
        <DataStateNotices
          metas={dataStateMetas}
          mockMessage="One or more portfolio management panels are using mock data. Do not treat affected values as live holdings or transactions."
        />

        <Panel title="Add Portfolio">
          <form action={createPortfolio} className="form-grid">
            <TextField className="field field-wide" id="name" label="Name" name="name" required />
            <TextField defaultValue="USD" id="base_currency" label="Base Currency" name="base_currency" required />
            <TextAreaField className="field field-full" id="description" label="Description" name="description" />
            <div className="button-row">
              <button type="submit">Add portfolio</button>
            </div>
          </form>
        </Panel>

        <Panel title="Set Opening Holding">
          <form action={createPortfolioHolding} className="form-grid">
            <PortfolioSelect id="holding-portfolio-id" portfolios={portfolios} />
            <CompanySelect companies={companies} id="holding-company-id" />
            <TextField id="holding-ticker" label="Ticker" name="ticker" required />
            <TextField defaultValue="USD" id="holding-currency" label="Currency" name="currency" required />
            <TextField id="holding-quantity" label="Quantity" min="0" name="quantity" required step="0.000001" type="number" />
            <TextField id="holding-average-cost" label="Average Cost" min="0" name="average_cost" required step="0.000001" type="number" />
            <TextField defaultValue={today} id="holding-as-of-date" label="As Of Date" name="as_of_date" required type="date" />
            <div className="button-row">
              <button disabled={portfolios.length === 0} type="submit">Set opening holding</button>
            </div>
          </form>
        </Panel>

        <Panel title="Record Security Activity">
          <form action={createPortfolioTransaction} className="form-grid">
            <PortfolioSelect id="transaction-portfolio-id" portfolios={portfolios} />
            <CompanySelect companies={companies} id="transaction-company-id" />
            <TextField id="transaction-ticker" label="Ticker" name="ticker" required />
            <SelectField defaultValue="buy" id="transaction-type" label="Type" name="transaction_type" required>
              {securityTransactionTypes.map((transactionType) => (
                <option key={transactionType} value={transactionType}>
                  {transactionTypeLabel(transactionType)}
                </option>
              ))}
            </SelectField>
            <TextField id="transaction-quantity" label="Quantity" min="0" name="quantity" required step="0.000001" type="number" />
            <TextField id="transaction-price" label="Price" min="0" name="price" required step="0.000001" type="number" />
            <TextField defaultValue="0" id="transaction-fees" label="Fees" min="0" name="fees" required step="0.000001" type="number" />
            <TextField defaultValue="USD" id="transaction-currency" label="Currency" name="currency" required />
            <TextField defaultValue={today} id="transaction-date" label="Date" name="transaction_date" required type="date" />
            <TextAreaField className="field field-wide" id="transaction-notes" label="Notes" name="notes" />
            <div className="button-row">
              <button disabled={portfolios.length === 0} type="submit">Record security activity</button>
            </div>
          </form>
        </Panel>

        <Panel title="Record Cash Activity">
          <form action={createPortfolioTransaction} className="form-grid">
            <PortfolioSelect id="cash-transaction-portfolio-id" portfolios={portfolios} />
            <input name="company_id" type="hidden" value="" />
            <input name="ticker" type="hidden" value="CASH" />
            <input name="price" type="hidden" value="0" />
            <input name="fees" type="hidden" value="0" />
            <SelectField defaultValue="deposit" id="cash-transaction-type" label="Type" name="transaction_type" required>
              {cashTransactionTypes.map((transactionType) => (
                <option key={transactionType} value={transactionType}>
                  {transactionTypeLabel(transactionType)}
                </option>
              ))}
            </SelectField>
            <TextField id="cash-transaction-amount" label="Amount" min="0" name="quantity" required step="0.01" type="number" />
            <TextField defaultValue="USD" id="cash-transaction-currency" label="Currency" name="currency" required />
            <TextField defaultValue={today} id="cash-transaction-date" label="Date" name="transaction_date" required type="date" />
            <TextAreaField className="field field-wide" id="cash-transaction-notes" label="Notes" name="notes" />
            <div className="button-row">
              <button disabled={portfolios.length === 0} type="submit">Record cash activity</button>
            </div>
          </form>
        </Panel>

        <Panel title="Portfolios">
          {portfolios.length === 0 ? (
            <EmptyState label="No portfolios yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Currency</th>
                    <th>Description</th>
                    <th>Total Value</th>
                    <th>Unrealized P&L</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolios.map((portfolio) => (
                    <tr key={portfolio.id}>
                      <td>{portfolio.name}</td>
                      <td>{portfolio.base_currency}</td>
                      <td>{portfolio.description ?? "-"}</td>
                      <td>
                        {valuationsById.get(portfolio.id)?.total_market_value != null
                          ? `${portfolio.base_currency} ${numberText(valuationsById.get(portfolio.id)!.total_market_value!)}`
                          : "-"}
                      </td>
                      <td>
                        {valuationsById.get(portfolio.id)?.total_unrealized_pnl != null
                          ? `${portfolio.base_currency} ${numberText(valuationsById.get(portfolio.id)!.total_unrealized_pnl!)}`
                          : "-"}
                      </td>
                      <td>
                        <div className="action-stack">
                          <Link className="button secondary-button" href={`/portfolio/${portfolio.id}`} style={{ padding: "0.25rem 0.5rem", fontSize: "0.875rem", textDecoration: "none", display: "inline-block", background: "var(--background-alt)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)" }}>
                            View Details
                          </Link>
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updatePortfolio} className="inline-form">
                              <input name="id" type="hidden" value={portfolio.id} />
                              <TextField defaultValue={portfolio.name} id={`portfolio-name-${portfolio.id}`} label="Name" name="name" required />
                              <TextField defaultValue={portfolio.base_currency} id={`portfolio-currency-${portfolio.id}`} label="Base Currency" name="base_currency" required />
                              <TextAreaField className="field field-full" defaultValue={portfolio.description ?? ""} id={`portfolio-description-${portfolio.id}`} label="Description" name="description" />
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <DeleteRecordForm action={deletePortfolioWithState} recordId={portfolio.id} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>



        <Panel title="Holdings">
          <div style={{ marginBottom: "1rem" }}>
            <DataFreshnessIndicator meta={holdingsRes.meta} source="Portfolio API" />
          </div>
          {holdings.length === 0 ? (
            <EmptyState label="No holdings yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Portfolio</th>
                    <th>Ticker</th>
                    <th>Company</th>
                    <th>Quantity</th>
                    <th>Average Cost</th>
                    <th>Market Price</th>
                    <th>Market Value</th>
                    <th>Unrealized P&L</th>
                    <th>Weight</th>
                    <th>As Of</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding) => {
                    const val = getHoldingValuation(holding.id, holding.portfolio_id);
                    return (
                    <tr key={holding.id}>
                      <td>{portfoliosById.get(holding.portfolio_id)?.name ?? `#${holding.portfolio_id}`}</td>
                      <td>{holding.ticker}</td>
                      <td>{companyLabel(holding.company_id, companiesById)}</td>
                      <td>{numberText(holding.quantity)}</td>
                      <td>
                        {holding.currency} {numberText(holding.average_cost)}
                      </td>
                      <td>
                        {val?.market_price != null ? (
                          <>
                            {holding.currency} {numberText(val.market_price)}
                            {val.is_stale_price && <span className="badge badge-warning" title="Stale price">⚠️</span>}
                          </>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td>
                        {val?.market_value != null ? `${holding.currency} ${numberText(val.market_value)}` : "-"}
                      </td>
                      <td>
                        {val?.unrealized_pnl != null ? (
                          <span style={{ color: val.unrealized_pnl >= 0 ? "var(--color-green-700)" : "var(--color-red-700)" }}>
                            {holding.currency} {numberText(val.unrealized_pnl)}
                            {val.unrealized_pnl_percent != null && ` (${numberText(val.unrealized_pnl_percent)}%)`}
                          </span>
                        ) : "-"}
                      </td>
                      <td>
                        {val?.weight_percent != null ? `${numberText(val.weight_percent)}%` : "-"}
                      </td>
                      <td>{holding.as_of_date}</td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updatePortfolioHolding} className="inline-form">
                              <input name="id" type="hidden" value={holding.id} />
                              <PortfolioSelect defaultValue={holding.portfolio_id} id={`holding-portfolio-${holding.id}`} portfolios={portfolios} />
                              <CompanySelect companies={companies} defaultValue={holding.company_id} id={`holding-company-${holding.id}`} />
                              <TextField defaultValue={holding.ticker} id={`holding-ticker-${holding.id}`} label="Ticker" name="ticker" required />
                              <TextField defaultValue={holding.currency} id={`holding-currency-${holding.id}`} label="Currency" name="currency" required />
                              <TextField defaultValue={holding.quantity} id={`holding-quantity-${holding.id}`} label="Quantity" min="0" name="quantity" required step="0.000001" type="number" />
                              <TextField defaultValue={holding.average_cost} id={`holding-average-cost-${holding.id}`} label="Average Cost" min="0" name="average_cost" required step="0.000001" type="number" />
                              <TextField defaultValue={holding.as_of_date} id={`holding-date-${holding.id}`} label="As Of Date" name="as_of_date" required type="date" />
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <DeleteRecordForm action={deletePortfolioHoldingWithState} recordId={holding.id} />
                        </div>
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        <Panel title="Transactions">
          {transactions.length === 0 ? (
            <EmptyState label="No transactions yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Portfolio</th>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Ticker</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Fees</th>
                    <th>Notes</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((transaction) => (
                    <tr key={transaction.id}>
                      <td>{portfoliosById.get(transaction.portfolio_id)?.name ?? `#${transaction.portfolio_id}`}</td>
                      <td>{transaction.transaction_date}</td>
                      <td><span className="badge">{transactionTypeLabel(transaction.transaction_type)}</span></td>
                      <td>{transaction.ticker}</td>
                      <td>{numberText(transaction.quantity)}</td>
                      <td>
                        {transaction.currency} {numberText(transaction.price)}
                      </td>
                      <td>{numberText(transaction.fees)}</td>
                      <td>{transaction.notes ?? "-"}</td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updatePortfolioTransaction} className="inline-form">
                              <input name="id" type="hidden" value={transaction.id} />
                              <PortfolioSelect defaultValue={transaction.portfolio_id} id={`transaction-portfolio-${transaction.id}`} portfolios={portfolios} />
                              <CompanySelect companies={companies} defaultValue={transaction.company_id} id={`transaction-company-${transaction.id}`} />
                              <TextField defaultValue={transaction.ticker} id={`transaction-ticker-${transaction.id}`} label="Ticker" name="ticker" required />
                              <SelectField defaultValue={transaction.transaction_type} id={`transaction-type-${transaction.id}`} label="Type" name="transaction_type" required>
                                {transactionTypes.map((transactionType) => (
                                  <option key={transactionType} value={transactionType}>
                                    {transactionTypeLabel(transactionType)}
                                  </option>
                                ))}
                              </SelectField>
                              <TextField defaultValue={transaction.quantity} id={`transaction-quantity-${transaction.id}`} label="Quantity" min="0" name="quantity" required step="0.000001" type="number" />
                              <TextField defaultValue={transaction.price} id={`transaction-price-${transaction.id}`} label="Price" min="0" name="price" required step="0.000001" type="number" />
                              <TextField defaultValue={transaction.fees} id={`transaction-fees-${transaction.id}`} label="Fees" min="0" name="fees" required step="0.000001" type="number" />
                              <TextField defaultValue={transaction.currency} id={`transaction-currency-${transaction.id}`} label="Currency" name="currency" required />
                              <TextField defaultValue={transaction.transaction_date} id={`transaction-date-${transaction.id}`} label="Date" name="transaction_date" required type="date" />
                              <TextAreaField className="field field-full" defaultValue={transaction.notes ?? ""} id={`transaction-notes-${transaction.id}`} label="Notes" name="notes" />
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <DeleteRecordForm action={deletePortfolioTransactionWithState} recordId={transaction.id} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        <div style={{ marginTop: "2rem" }}>
          <h3 style={{ marginBottom: "1rem" }}>CSV Imports</h3>
          <div className="metric-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
            <CsvImporter title="Import Portfolio Holdings" endpoint="/import/portfolio-holdings" />
            <CsvImporter title="Import Portfolio Transactions" endpoint="/import/portfolio-transactions" />
          </div>
        </div>
      </>
    );
  } catch (error: any) {
    console.error("PAGE RENDER ERROR:", error);
    return (
      <>
        <PageHeader eyebrow="Portfolio" title="Portfolio" />
        <ErrorState message={`Could not load portfolio records from the backend API. Error: ${error?.message || error}`} />
      </>
    );
  }
}
