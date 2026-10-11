import { createMacroObservation, createMacroSeries, deleteMacroSeriesWithState, importFredSeries } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { MacroBottomUpForm } from "@/components/macro/macro-bottom-up-form";
import { MacroScenarioForm, MarketControls } from "@/components/macro/macro-scenario-form";
import { MacroSensitivityTable } from "@/components/macro/macro-sensitivity-table";
import { MacroTopDownForm } from "@/components/macro/macro-top-down-form";
import { ClaimTypeBadges, MacroLimitationsNotice, MacroWorkbenchTabs } from "@/components/macro/macro-workbench";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataFreshnessIndicator, DataStateNotices, NotConfiguredState } from "@/components/ui/data-states";
import { ApiError } from "@/lib/api";
import { serverFetchApi, serverFetchApiResponse, serverPostApiResponse } from "@/lib/server-api";
import type {
  ApiResponse,
  ApiMeta,
  MacroScenarioResult,
  MacroSectorSensitivity,
  MacroSeries,
  MacroSensitivityResult,
  BottomUpMacroSegment,
  TopDownMacroPeriod,
  ProviderHealthRead
} from "@/lib/api";
import { normalizeMacroWorkbenchTab } from "@/lib/macro-workbench";

type MacroPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

const DEFAULT_MARKET = "IN";
const DEFAULT_COUNTRY = "India";

function firstParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function stringParam(params: Record<string, string | string[] | undefined>, key: string, fallback = "") {
  return firstParam(params[key])?.trim() || fallback;
}

function numberParam(params: Record<string, string | string[] | undefined>, key: string, fallback = 0) {
  const value = Number(stringParam(params, key));
  return Number.isFinite(value) ? value : fallback;
}

function stringParams(params: Record<string, string | string[] | undefined>) {
  return Object.fromEntries(
    Object.entries(params).map(([key, value]) => [key, firstParam(value)?.trim() || ""])
  );
}

function formatNumber(value: number | null | undefined, digits = 4) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return value.toLocaleString("en-US", { maximumFractionDigits: digits });
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return `${(value * 100).toFixed(2)}%`;
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }
  return error instanceof Error ? error.message : "Could not load macro result.";
}

function ScenarioResult({ result }: { result: MacroScenarioResult }) {
  return (
    <div className="brief-list">
      <div className="metric-grid">
        <div className="metric">
          <div className="metric-label">Value Impact</div>
          <div className="metric-value">{formatPercent(result.estimated_value_impact_pct)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Operating Income Impact</div>
          <div className="metric-value">{formatPercent(result.estimated_operating_income_impact_pct)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Confidence</div>
          <div className="metric-value">{result.confidence}</div>
        </div>
      </div>
      {result.warnings.length > 0 ? (
        <div className="section-block">
          <strong>Warnings</strong>
          <ul>
            {result.warnings.map((warning) => <li key={warning}>{warning}</li>)}
          </ul>
        </div>
      ) : null}
      <p className="muted">{result.formula}</p>
    </div>
  );
}

function BottomUpResult({ result }: { result: MacroSensitivityResult }) {
  return (
    <div className="brief-list">
      <div className="metric-grid">
        <div className="metric">
          <div className="metric-label">Weighted Duration</div>
          <div className="metric-value">{formatNumber(result.firm_value.duration)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Cyclicality</div>
          <div className="metric-value">{formatNumber(result.firm_value.cyclicality)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Confidence</div>
          <div className="metric-value">{result.confidence_label}</div>
        </div>
      </div>
      {result.warnings && result.warnings.length > 0 ? (
        <ul>
          {result.warnings.map((warning: string) => <li key={warning}>{warning}</li>)}
        </ul>
      ) : null}
    </div>
  );
}

function TopDownResult({ result }: { result: MacroSensitivityResult }) {
  return (
    <div className="brief-list">
      <div className="metric-grid">
        <div className="metric">
          <div className="metric-label">Observations</div>
          <div className="metric-value">{result.observation_count}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Firm Value Duration</div>
          <div className="metric-value">{formatNumber(result.firm_value.duration)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Confidence</div>
          <div className="metric-value">{result.confidence_label}</div>
        </div>
      </div>
      {result.warnings && result.warnings.length > 0 ? (
        <ul>
          {result.warnings.map((warning: string) => <li key={warning}>{warning}</li>)}
        </ul>
      ) : null}
    </div>
  );
}

export default async function MacroPage({ searchParams }: MacroPageProps) {
  const query = (await searchParams) ?? {};
  const market = stringParam(query, "market", DEFAULT_MARKET);
  const country = stringParam(query, "country", market === "IN" ? DEFAULT_COUNTRY : "United States");
  const sic = stringParam(query, "sic");
  const run = stringParam(query, "run");
  const activeTab = normalizeMacroWorkbenchTab(query.tab);
  const values = stringParams(query);

  try {
    const [seriesListRes, providerHealthRes] = await Promise.all([
      serverFetchApiResponse<MacroSeries[]>("/macro"),
      serverFetchApiResponse<ProviderHealthRead[]>("/api/providers/health").catch(() => ({ data: [], meta: null })),
    ]);
    const seriesList = seriesListRes.data || [];

    let sectorResult: MacroSectorSensitivity | null = null;
    let scenarioResult: MacroScenarioResult | null = null;
    let bottomUpResult: MacroSensitivityResult | null = null;
    let topDownResult: MacroSensitivityResult | null = null;
    let workbenchError: string | null = null;

    const metas: ApiMeta[] = [];
    if (seriesListRes.meta) metas.push(seriesListRes.meta);

    if (providerHealthRes.meta) metas.push(providerHealthRes.meta);
    const fredConfigured = (providerHealthRes.data || [])
      .find((provider) => provider.provider_name === "FRED")?.configured ?? false;

    if (sic) {
      try {
        const sectorQuery = new URLSearchParams({ market, country, sic });
        const res = await serverFetchApiResponse<MacroSectorSensitivity>(`/api/valuation/macro/sector?${sectorQuery.toString()}`);
        sectorResult = res.data;
        if (res.meta) metas.push(res.meta);
      } catch (error) {
        workbenchError = errorMessage(error);
      }
    }

    if (run === "scenario" && sic) {
      try {
        const res = await serverPostApiResponse<MacroScenarioResult>("/api/valuation/macro/scenario", {
          market,
          country,
          sic_code: sic,
          rate_shock: numberParam(query, "rate_shock"),
          gdp_shock: numberParam(query, "gdp_shock"),
          inflation_shock: numberParam(query, "inflation_shock"),
          currency_shock: numberParam(query, "currency_shock"),
          currencyVariableDirection: stringParam(query, "currency_variable_direction") || null
        });
        scenarioResult = res.data;
        if (res.meta) metas.push(res.meta);
      } catch (error) {
        workbenchError = errorMessage(error);
      }
    }

    if (run === "bottom-up") {
      const segments: BottomUpMacroSegment[] = [1, 2, 3]
        .map((index) => ({
          segment_name: stringParam(query, `segment_${index}_name`),
          sic_code: stringParam(query, `segment_${index}_sic`),
          segment_value: numberParam(query, `segment_${index}_value`)
        }))
        .filter((segment) => segment.segment_name && segment.sic_code && segment.segment_value && segment.segment_value > 0);
      if (segments.length > 0) {
        try {
          const res = await serverPostApiResponse<MacroSensitivityResult>("/api/valuation/macro/bottom-up", {
            market,
            country,
            segments: segments.map((segment) => ({
              name: segment.segment_name,
              sicCode: segment.sic_code,
              value: segment.segment_value,
            })),
          });
          bottomUpResult = res.data;
          if (res.meta) metas.push(res.meta);
        } catch (error) {
          workbenchError = errorMessage(error);
        }
      }
    }

    if (run === "top-down") {
      const periods: TopDownMacroPeriod[] = [1, 2, 3]
        .map((index) => ({
          period_label: stringParam(query, `period_${index}`),
          operating_income: numberParam(query, `operating_income_${index}`),
          market_cap: numberParam(query, `market_cap_${index}`),
          total_debt: numberParam(query, `total_debt_${index}`),
          change_in_long_term_bond_rate: numberParam(query, `rate_change_${index}`),
          gdp_growth: numberParam(query, `gdp_growth_${index}`),
          inflation_change: numberParam(query, `inflation_change_${index}`),
          currency_change: numberParam(query, `currency_change_${index}`)
        }))
        .filter((period) => period.period_label);
      if (periods.length >= 3) {
        try {
          const res = await serverPostApiResponse<MacroSensitivityResult>("/api/valuation/macro/top-down", {
            frequency: "annual",
            periods: periods.map((period) => ({
              period: period.period_label,
              operating_income: period.operating_income,
              market_cap: period.market_cap,
              total_debt: period.total_debt,
              enterprise_value: period.enterprise_value,
              change_in_long_term_bond_rate: period.change_in_long_term_bond_rate,
              gdp_growth: period.gdp_growth,
              inflation_change: period.inflation_change,
              currency_change: period.currency_change,
            })),
          });
          topDownResult = res.data;
          if (res.meta) metas.push(res.meta);
        } catch (error) {
          workbenchError = errorMessage(error);
        }
      }
    }

    return (
      <>
        <PageHeader eyebrow="Economic Data" title="Macro Workbench" status={`${seriesList.length} series`} />
        <DataStateNotices
          metas={metas}
          mockMessage="Macro series data is mocked. Do not use it for valuation sensitivity until source-backed data is configured."
        />
        <MacroWorkbenchTabs activeTab={activeTab} />
        <ClaimTypeBadges />
        <MacroLimitationsNotice />

        {activeTab === "sector" && <Panel title="Sector Sensitivity">
          <form className="form-grid" method="get">
            <input name="tab" type="hidden" value="sector" />
            <MarketControls country={country} market={market} sic={sic} />
            <div className="button-row">
              <button type="submit">Load Sector</button>
            </div>
          </form>
          {workbenchError && !sectorResult ? (
            <NotConfiguredState
              title="Not available yet"
              description={`${market}/${country} macro benchmark is not available for SIC ${sic || "the selected sector"}. ${workbenchError}`}
            />
          ) : null}
          {sectorResult ? <MacroSensitivityTable result={sectorResult} /> : !workbenchError ? <EmptyState label="Select a market and SIC to load real benchmark data." /> : null}
          {seriesListRes.meta ? <DataFreshnessIndicator meta={seriesListRes.meta} /> : null}
        </Panel>}

        {activeTab === "scenario" && <Panel title="Macro Shock Scenario">
          <MacroScenarioForm country={country} market={market} sic={sic} values={values} />
          {scenarioResult ? <ScenarioResult result={scenarioResult} /> : <EmptyState label="Run a scenario to estimate source-backed sector impact." />}
        </Panel>}

        {activeTab === "bottom-up" && <Panel title="Bottom-Up Segment Sensitivity">
          <MacroBottomUpForm country={country} market={market} sic={sic} values={values} />
          {bottomUpResult ? <BottomUpResult result={bottomUpResult} /> : <EmptyState label="Enter one or more SIC-backed segments to calculate weighted exposure." />}
        </Panel>}

        {activeTab === "top-down" && <Panel title="Top-Down Company History">
          <MacroTopDownForm country={country} market={market} sic={sic} values={values} />
          {topDownResult ? <TopDownResult result={topDownResult} /> : <EmptyState label="Enter at least three periods to estimate company-specific macro sensitivity." />}
        </Panel>}

        {activeTab === "series" && <><Panel title="Import from FRED">
          {fredConfigured ? (
            <form action={importFredSeries} className="form-grid">
              <TextField id="series_id" label="FRED Series ID" name="series_id" placeholder="e.g. CPIAUCSL or FEDFUNDS" required />
              <div className="button-row" style={{ gridColumn: "1 / -1" }}>
                <button type="submit">Import Series & Observations</button>
              </div>
              <p className="text-sm text-gray-500 mt-2" style={{ gridColumn: "1 / -1" }}>
                Requires FRED API key. Use only for configured US macro series.
              </p>
            </form>
          ) : (
            <NotConfiguredState
              title="FRED Integration Not Configured"
              description="Set FRED_API_KEY in your environment variables to import source-backed economic data directly from the Federal Reserve."
            />
          )}
        </Panel>

        <Panel title="Add Macro Series Manually">
          <form action={createMacroSeries} className="form-grid">
            <TextField id="name" label="Series Name" name="name" placeholder="India 10Y Yield" required />
            <TextField id="units" label="Units" name="units" placeholder="%" />
            <TextField id="frequency" label="Frequency" name="frequency" placeholder="Monthly" />
            <TextAreaField className="field field-full" id="description" label="Description" name="description" />
            <div className="button-row">
              <button type="submit">Add Series</button>
            </div>
          </form>
        </Panel>

        <Panel title="Add Observation">
          <form action={createMacroObservation} className="form-grid">
            <SelectField id="series_id" label="Series" name="series_id" required>
              <option value="">Select series...</option>
              {seriesList.map((series) => (
                <option key={series.id} value={series.id}>
                  {series.name}
                </option>
              ))}
            </SelectField>
            <TextField id="date_recorded" label="Date" name="date_recorded" type="date" required />
            <TextField id="value" label="Value" name="value" type="number" step="any" required />
            <div className="button-row">
              <button type="submit">Add Observation</button>
            </div>
          </form>
        </Panel>

        <Panel title="Series & Data">
          {seriesList.length === 0 ? (
            <EmptyState label="No macro series tracked yet." />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {seriesList.map((series) => (
                <div key={series.id} className="border border-gray-200 rounded p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-medium">{series.name}</h3>
                    <DeleteRecordForm action={deleteMacroSeriesWithState} recordId={series.id} />
                  </div>
                  {series.description && <p className="text-sm text-gray-600 mb-2">{series.description}</p>}
                  <div className="text-xs text-gray-500 mb-4 flex gap-4">
                    <span>Units: {series.units || "N/A"}</span>
                    <span>Freq: {series.frequency || "N/A"}</span>
                    <span>Source: {series.provider_name || "Manual"}</span>
                  </div>
                  {series.source_url ? (
                    <p className="text-sm mb-4">
                      <a className="text-link" href={series.source_url} rel="noreferrer" target="_blank">
                        Open provider series
                      </a>
                    </p>
                  ) : null}

                  <h4 className="text-sm font-medium mb-2 border-b pb-1">Observations</h4>
                  {series.observations.length === 0 ? (
                    <p className="text-sm text-gray-500">No data points yet.</p>
                  ) : (
                    <div className="max-h-48 overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-gray-500">
                            <th className="font-normal pb-1">Record</th>
                            <th className="font-normal pb-1">Date</th>
                            <th className="font-normal pb-1 text-right">Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[...series.observations].sort((a, b) => new Date(b.date_recorded).getTime() - new Date(a.date_recorded).getTime()).map((obs) => (
                            <tr key={obs.id} className="border-t border-gray-100">
                              <td className="py-1">#{obs.id}</td>
                              <td className="py-1">{obs.date_recorded}</td>
                              <td className="py-1 text-right">{obs.value}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Panel>
        </>}
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Economic Data" title="Macro Workbench" />
        <ErrorState message="Could not load macro data from the backend API." />
      </>
    );
  }
}
