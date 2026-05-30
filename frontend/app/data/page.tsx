import Link from "next/link";
import { PageHeader, Panel } from "@/components/page";
import { fetchRssFeed, fetchRecentSecFilings } from "@/app/actions";
import { SelectField, TextField, CheckboxField } from "@/components/form-fields";
import { fetchApi } from "@/lib/api";
import type { Company, Source } from "@/lib/api";

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
  const [companies, sources] = await Promise.all([
    fetchApi<Company[]>("/companies").catch(() => []),
    fetchApi<Source[]>("/sources").catch(() => [])
  ]);

  return (
    <>
      <PageHeader eyebrow="Data & APIs" title="Data Management" />
      
      <div className="metric-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <Panel title="Sources">
          <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
            Manage RSS feeds, SEC ingestion configs, and source reliability.
          </p>
          <div className="button-row">
            <Link href="/sources" passHref>
              <button>Manage Sources</button>
            </Link>
          </div>
        </Panel>
        
        <Panel title="Market Prices">
          <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
            View and manage manual or imported market prices.
          </p>
          <div className="button-row">
            <Link href="/market-prices" passHref>
              <button>Manage Prices</button>
            </Link>
          </div>
        </Panel>

        <Panel title="Macro Data">
          <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
            Track macroeconomic series, indicators, and CSV imports.
          </p>
          <div className="button-row">
            <Link href="/macro" passHref>
              <button>Manage Macro Data</button>
            </Link>
          </div>
        </Panel>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <Panel title="Fetch RSS Feed">
          <form action={fetchRssFeed} className="form-grid">
            <SelectField disabled={sources.length === 0} id="rss-feed-source-id" label="Source" name="source_id" required>
              <option value="">Select RSS source</option>
              {sourceOptions(sources)}
            </SelectField>
            <SelectField id="rss-feed-company-id" label="Company" name="company_id">
              <option value="">Infer from title</option>
              {companyOptions(companies)}
            </SelectField>
            <TextField className="field field-wide" id="feed-url" label="Feed URL" name="feed_url" placeholder="Uses source Base URL if blank" type="url" />
            <div className="button-row">
              <button disabled={sources.length === 0} type="submit">Fetch RSS feed</button>
            </div>
          </form>
        </Panel>

        <Panel title="Fetch Recent SEC Filings">
          <form action={fetchRecentSecFilings} className="form-grid">
            <SelectField disabled={sources.length === 0} id="sec-fetch-source-id" label="Source" name="source_id" required>
              <option value="">Select SEC source</option>
              {sourceOptions(sources)}
            </SelectField>
            <SelectField disabled={companies.length === 0} id="sec-fetch-company-id" label="Company" name="company_id" required>
              <option value="">Select company with CIK</option>
              {companyOptions(companies)}
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
              <button disabled={sources.length === 0 || companies.length === 0} type="submit">Fetch recent SEC filings</button>
            </div>
          </form>
        </Panel>
      </div>
    </>
  );
}
