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
import { fetchApi } from "@/lib/api";
import type { Company, Portfolio, PortfolioHolding, PortfolioTransaction, PortfolioValuation, PortfolioAnalytics } from "@/lib/api";
import { PortfolioAnalyticsDashboard } from "@/components/portfolio-analytics";
import { CsvImporter } from "@/components/csv-importer";

const transactionTypes = [
  "buy",
  "sell",
  "dividend",
  "split",
  "bonus",
  "deposit",
  "withdrawal",
  "fee",
  "tax",
  "manual_adjustment"
];

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
    const [portfolios, holdings, transactions, companies] = await Promise.all([
      fetchApi<Portfolio[]>("/portfolios"),
      fetchApi<PortfolioHolding[]>("/portfolio-holdings"),
      fetchApi<PortfolioTransaction[]>("/portfolio-transactions"),
      fetchApi<Company[]>("/companies")
    ]);
    const today = new Date().toISOString().slice(0, 10);
    const portfoliosById = new Map(portfolios.map((portfolio) => [portfolio.id, portfolio]));
    const companiesById = new Map(companies.map((company) => [company.id, company]));

    const valuations = await Promise.all(
      portfolios.map((portfolio) =>
        fetchApi<PortfolioValuation>(`/portfolios/${portfolio.id}/valuation`).catch(() => null)
      )
    );
    const valuationsById = new Map(
      valuations.filter(Boolean).map((v) => [v!.portfolio_id, v!])
    );

    const getHoldingValuation = (holdingId: number, portfolioId: number) => {
      const val = valuationsById.get(portfolioId);
      if (!val) return null;
      return val.holdings.find(h => h.holding_id === holdingId) || null;
    };

    const analyticsResults = await Promise.all(
      portfolios.map((portfolio) =>
        fetchApi<PortfolioAnalytics>(`/portfolios/${portfolio.id}/analytics`).catch(() => null)
      )
    );
    const validAnalytics = analyticsResults.filter((a): a is PortfolioAnalytics => a !== null);

    return (
      <>
        <PageHeader eyebrow="Portfolio" title="Portfolio" status={`${portfolios.length} portfolios`} />

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

        <Panel title="Add Holding">
          <form action={createPortfolioHolding} className="form-grid">
            <PortfolioSelect id="holding-portfolio-id" portfolios={portfolios} />
            <CompanySelect companies={companies} id="holding-company-id" />
            <TextField id="holding-ticker" label="Ticker" name="ticker" required />
            <TextField defaultValue="USD" id="holding-currency" label="Currency" name="currency" required />
            <TextField id="holding-quantity" label="Quantity" min="0" name="quantity" required step="0.000001" type="number" />
            <TextField id="holding-average-cost" label="Average Cost" min="0" name="average_cost" required step="0.000001" type="number" />
            <TextField defaultValue={today} id="holding-as-of-date" label="As Of Date" name="as_of_date" required type="date" />
            <div className="button-row">
              <button disabled={portfolios.length === 0} type="submit">Add holding</button>
            </div>
          </form>
        </Panel>

        <Panel title="Add Transaction">
          <form action={createPortfolioTransaction} className="form-grid">
            <PortfolioSelect id="transaction-portfolio-id" portfolios={portfolios} />
            <CompanySelect companies={companies} id="transaction-company-id" />
            <TextField id="transaction-ticker" label="Ticker" name="ticker" required />
            <SelectField defaultValue="buy" id="transaction-type" label="Type" name="transaction_type" required>
              {transactionTypes.map((transactionType) => (
                <option key={transactionType} value={transactionType}>
                  {transactionType}
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
              <button disabled={portfolios.length === 0} type="submit">Add transaction</button>
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
                        {valuationsById.get(portfolio.id)?.total_portfolio_value != null
                          ? `${portfolio.base_currency} ${numberText(valuationsById.get(portfolio.id)!.total_portfolio_value!)}`
                          : valuationsById.get(portfolio.id)?.total_market_value != null
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

        {validAnalytics.map(analytics => {
          const portfolioName = portfoliosById.get(analytics.portfolio_id)?.name ?? `#${analytics.portfolio_id}`;
          return (
            <Panel key={analytics.portfolio_id} title={`Analytics: ${portfolioName}`}>
              <PortfolioAnalyticsDashboard analytics={analytics} />
            </Panel>
          );
        })}

        <Panel title="Exposure Summary">
          {portfolios.map(portfolio => {
            const portfolioHoldings = holdings.filter(h => h.portfolio_id === portfolio.id);
            if (portfolioHoldings.length === 0) return null;

            // Group by tag
            const tagExposures = new Map<string, { value: number, percent: number }>();
            let untaggedValue = 0;
            let untaggedPercent = 0;
            const val = valuationsById.get(portfolio.id);
            
            if (val) {
              for (const h of portfolioHoldings) {
                const company = companiesById.get(h.company_id!);
                const hVal = val.holdings.find(vh => vh.holding_id === h.id);
                if (!hVal || hVal.market_value == null || hVal.weight_percent == null) continue;
                
                if (!company || !company.exposure_tags || company.exposure_tags.length === 0) {
                  untaggedValue += hVal.market_value;
                  untaggedPercent += hVal.weight_percent;
                } else {
                  for (const tag of company.exposure_tags) {
                    const current = tagExposures.get(tag.name) || { value: 0, percent: 0 };
                    tagExposures.set(tag.name, {
                      value: current.value + hVal.market_value,
                      percent: current.percent + hVal.weight_percent
                    });
                  }
                }
              }
            }
            
            const sortedTags = Array.from(tagExposures.entries()).sort((a, b) => b[1].percent - a[1].percent);

            return (
              <div key={`exp-${portfolio.id}`} className="mb-8 last:mb-0">
                <h3 className="text-lg font-medium mb-4">{portfolio.name} Exposures</h3>
                {sortedTags.length === 0 && untaggedValue === 0 ? (
                  <p className="text-sm text-gray-500">No exposure data calculated.</p>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Exposure Tag</th>
                          <th className="text-right">Value ({portfolio.base_currency})</th>
                          <th className="text-right">Weight</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortedTags.map(([tagName, data]) => (
                          <tr key={tagName}>
                            <td>{tagName}</td>
                            <td className="text-right">{numberText(data.value)}</td>
                            <td className="text-right">{numberText(data.percent)}%</td>
                          </tr>
                        ))}
                        {untaggedValue > 0 && (
                          <tr className="text-gray-500">
                            <td><em>Untagged</em></td>
                            <td className="text-right">{numberText(untaggedValue)}</td>
                            <td className="text-right">{numberText(untaggedPercent)}%</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </Panel>

        <Panel title="Holdings">
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
                      <td><span className="badge">{transaction.transaction_type}</span></td>
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
                                    {transactionType}
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
  } catch {
    return (
      <>
        <PageHeader eyebrow="Portfolio" title="Portfolio" />
        <ErrorState message="Could not load portfolio records from the backend API." />
      </>
    );
  }
}
