import { RetainedActionForm } from "@/components/retained-action-form";
import Link from "next/link";
import { DataStateNotices, PageHeader, Panel } from "@/components/page";
import { fetchRssFeed, fetchRecentSecFilings } from "@/app/actions";
import { SelectField, TextField, CheckboxField } from "@/components/form-fields";
import { SourceCapabilityMatrix } from "@/components/source-capability-matrix";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, Source, SourceCapability } from "@/lib/api";

function sourceOptions(sources: Source[]) {
  return sources.map((source) => (
    <option key={source.id} value={source.id}>
      {source.name}
    </option>
  ));
}

function companyOptions(companies: Company[]) {
  return companies.map((company) => (
    <option key={company.id} value={company.id}>
      {company.ticker}
    </option>
  ));
}

export default async function DataPage() {
  const [companiesRes, sourcesRes, usCapabilitiesRes, indiaCapabilitiesRes] = await Promise.all([
    serverFetchApiResponse<Company[]>("/companies"),
    serverFetchApiResponse<Source[]>("/sources"),
    serverFetchApiResponse<SourceCapability[]>("/api/source-capabilities?market=US"),
    serverFetchApiResponse<SourceCapability[]>("/api/source-capabilities?market=IN")
  ]);
  const companies = companiesRes.data || [];
  const sources = sourcesRes.data || [];
  const activeRssSources = sources.filter((source) => source.active && source.source_type === "rss");
  const preferredSecSource = sources.find(
    (source) => source.active && (source.source_type === "sec" || source.source_type === "filing")
  );
  const secCompanies = companies.filter(
    (company) => company.active && company.market !== "IN" && Boolean(company.cik)
  );
  const usCapabilities = usCapabilitiesRes.data || [];
  const indiaCapabilities = indiaCapabilitiesRes.data || [];
  return (
    <>
      <PageHeader eyebrow="Data & APIs" title="Data Management" />
      <DataStateNotices
        metas={[companiesRes.meta, sourcesRes.meta, usCapabilitiesRes.meta, indiaCapabilitiesRes.meta]}
        mockMessage="One or more data management panels are using mock data. Configure real sources before relying on those workflows."
      />

      <Panel title="US / India Source Capability Matrix">
        <p className="muted">Adapter support and configuration only. Check Data Health for recent failures and each company or portfolio for missing prices, FX and reviewed financials.</p>
        <SourceCapabilityMatrix usCapabilities={usCapabilities} indiaCapabilities={indiaCapabilities} />
      </Panel>

      <div className="metric-grid data-management-grid">
        <Panel title="Sources">
          <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
            Manage RSS feeds, SEC ingestion configs, and source reliability.
          </p>
          <div className="button-row">
            <Link className="secondary-button" href="/sources">Manage Sources</Link>
          </div>
        </Panel>

        <Panel title="Market Prices">
          <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
            View and manage manual or imported market prices.
          </p>
          <div className="button-row">
            <Link className="secondary-button" href="/market-prices">Manage Prices</Link>
          </div>
        </Panel>

        <Panel title="Macro Data">
          <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
            Track macroeconomic series, indicators, and CSV imports.
          </p>
          <div className="button-row">
            <Link className="secondary-button" href="/macro">Manage Macro Data</Link>
          </div>
        </Panel>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <Panel title="Fetch RSS Feed">
          <RetainedActionForm label="Fetch rss feed" action={fetchRssFeed} className="form-grid">
            <SelectField disabled={activeRssSources.length === 0} id="rss-feed-source-id" label="Source" name="source_id" required>
              <option value="">Select RSS source</option>
              {sourceOptions(activeRssSources)}
            </SelectField>
            <SelectField id="rss-feed-company-id" label="Company" name="company_id">
              <option value="">Infer from title</option>
              {companyOptions(companies)}
            </SelectField>
            <TextField className="field field-wide" id="feed-url" label="Feed URL" name="feed_url" placeholder="Uses source Base URL if blank" type="url" />
            <div className="button-row">
              <button disabled={activeRssSources.length === 0} type="submit">Fetch RSS feed</button>
            </div>
          </RetainedActionForm>
        </Panel>

        <Panel title="Fetch Recent SEC Filings">
          <RetainedActionForm label="Fetch recent sec filings" action={fetchRecentSecFilings} className="form-grid">
            {preferredSecSource && <input name="source_id" type="hidden" value={preferredSecSource.id} />}
            <div className="field">
              <span className="field-label">SEC Source</span>
              <strong>{preferredSecSource?.name ?? "SEC EDGAR (automatic)"}</strong>
            </div>
            <SelectField disabled={secCompanies.length === 0} id="sec-fetch-company-id" label="Company" name="company_id" required>
              <option value="">Select company with CIK</option>
              {companyOptions(secCompanies)}
            </SelectField>
            <TextField defaultValue="40" id="sec-fetch-limit" label="Limit" min="1" name="limit" type="number" />
            <SelectField defaultValue="" id="sec-fetch-form-type" label="Form" name="form_type">
              <option value="">10-K, 10-Q, 8-K</option>
              <option value="10-K">10-K</option>
              <option value="10-Q">10-Q</option>
              <option value="8-K">8-K</option>
            </SelectField>
            <TextField id="sec-fetch-filing-year" label="Filing Year" min="1994" name="filing_year" placeholder="Optional" type="number" />
            <CheckboxField checkboxLabel="Download filing text" className="field field-wide" id="sec-fetch-download-text" label="Filing Text" name="download_text" />
            <div className="button-row">
              <button disabled={secCompanies.length === 0} type="submit">Fetch recent SEC filings</button>
            </div>
          </RetainedActionForm>
        </Panel>
      </div>
    </>
  );
}
