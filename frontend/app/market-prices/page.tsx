import {
  createMarketPrice,
  deleteMarketPriceWithState,
  updateMarketPrice
} from "@/app/actions";
import { CsvImporter } from "@/components/csv-importer";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices, DataFreshnessIndicator } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, MarketPrice } from "@/lib/api";
import { marketPriceSource, marketPriceTiming } from "@/lib/market-price-provenance";

function numberText(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 6 });
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

function companyLabel(companyId: number | null, companiesById: Map<number, Company>): string {
  if (companyId === null) {
    return "-";
  }
  return companiesById.get(companyId)?.ticker ?? `#${companyId}`;
}

export default async function MarketPricesPage() {
  try {
    const [pricesRes, companiesRes] = await Promise.all([
      serverFetchApiResponse<MarketPrice[]>("/market-prices"),
      serverFetchApiResponse<Company[]>("/companies")
    ]);
    const prices = pricesRes.data || [];
    const companies = companiesRes.data || [];
    const today = new Date().toISOString().slice(0, 10);
    const companiesById = new Map(companies.map((company) => [company.id, company]));

    return (
      <>
        <PageHeader eyebrow="Market Data" title="Market Prices" status={`${prices.length} prices`} />
        <DataStateNotices
          metas={[pricesRes.meta, companiesRes.meta]}
          mockMessage="Market price data is mocked. Do not use affected prices for valuation or portfolio exposure."
        />
        <Panel title="Add Market Price">
          <form action={createMarketPrice} className="form-grid">
            <CompanySelect companies={companies} id="price-company-id" />
            <TextField id="price-ticker" label="Ticker" name="ticker" required />
            <TextField id="price-price" label="Price" min="0" name="price" required step="0.000001" type="number" />
            <TextField defaultValue="USD" id="price-currency" label="Currency" name="currency" required />
            <TextField defaultValue={today} id="price-date" label="As Of Date" name="as_of_date" required type="date" />
            <div className="button-row">
              <button type="submit">Add price</button>
            </div>
          </form>
        </Panel>

        <Panel title="Prices">
          <div style={{ marginBottom: "1rem" }}>
            <DataFreshnessIndicator meta={pricesRes.meta} source="Market Prices API" />
          </div>
          {prices.length === 0 ? (
            <EmptyState label="No market prices yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Company</th>
                    <th>Price</th>
                    <th>As Of</th>
                    <th>Source</th>
                    <th>Timing</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {prices.map((price) => {
                    const source = marketPriceSource(price);
                    const warnings = price.warnings || [];
                    return (
                      <tr key={price.id}>
                        <td>{price.ticker}</td>
                        <td>{companyLabel(price.company_id, companiesById)}</td>
                        <td>
                          {price.currency} {numberText(price.price)}
                        </td>
                        <td>{price.as_of_date}</td>
                        <td>
                          <span className={`badge${source.tone === "success" ? " badge-success" : source.tone === "warning" ? " badge-warn" : ""}`}>
                            {source.label}
                          </span>
                          {price.provider_symbol ? <div className="muted">{price.provider_symbol}</div> : null}
                          {warnings.length > 0 ? (
                            <details>
                              <summary>{warnings.length} warning{warnings.length === 1 ? "" : "s"}</summary>
                              <ul>
                                {warnings.map((warning) => <li key={warning}>{warning}</li>)}
                              </ul>
                            </details>
                          ) : null}
                        </td>
                        <td>
                          <div>{marketPriceTiming(price)}</div>
                          {price.source_timestamp || price.observed_at ? (
                            <div className="muted">
                              {price.source_timestamp ? "Source" : "Observed"}: {price.source_timestamp || price.observed_at}
                            </div>
                          ) : null}
                        </td>
                        <td>
                          <div className="action-stack">
                            <details className="edit-panel">
                              <summary>Edit</summary>
                              <form action={updateMarketPrice} className="inline-form">
                                <input name="id" type="hidden" value={price.id} />
                                <CompanySelect companies={companies} defaultValue={price.company_id} id={`price-company-${price.id}`} />
                                <TextField defaultValue={price.ticker} id={`price-ticker-${price.id}`} label="Ticker" name="ticker" required />
                                <TextField defaultValue={price.price} id={`price-price-${price.id}`} label="Price" min="0" name="price" required step="0.000001" type="number" />
                                <TextField defaultValue={price.currency} id={`price-currency-${price.id}`} label="Currency" name="currency" required />
                                <TextField defaultValue={price.as_of_date} id={`price-date-${price.id}`} label="As Of Date" name="as_of_date" required type="date" />
                                <div className="button-row">
                                  <button className="secondary-button" type="submit">Save</button>
                                </div>
                              </form>
                            </details>
                            <DeleteRecordForm action={deleteMarketPriceWithState} recordId={price.id} />
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

        <div style={{ marginTop: "2rem" }}>
          <h3 style={{ marginBottom: "1rem" }}>CSV Imports</h3>
          <div className="metric-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
            <CsvImporter title="Import Market Prices" endpoint="/import/market-prices" />
          </div>
        </div>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Market Data" title="Market Prices" />
        <ErrorState message="Could not load market prices from the backend API." />
      </>
    );
  }
}
