import { RetainedActionForm } from "@/components/retained-action-form";
import { hasUsableData } from "@/lib/data-state-meta";
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
import { serverFetchApiResponse, serverPostApiResponse } from "@/lib/server-api";
import type {
  ApiResponse,
  ApiMeta,
  MacroScenarioResult,
  MacroSectorSensitivity,
  MacroSeries,
  MacroSensitivityResult,
  ProviderHealthRead
} from "@/lib/api";
import { normalizeMacroWorkbenchTab, macroNumber, macroPeriodCount, macroTopDownPeriods, macroBottomUpSegments } from "@/lib/macro-workbench";
import { ScenarioResult, TopDownResult, BottomUpResult } from "@/components/macro/macro-results";

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

function stringParams(params: Record<string, string | string[] | undefined>) {
  return Object.fromEntries(
    Object.entries(params).map(([key, value]) => [key, firstParam(value)?.trim() || ""])
  );
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Could not load macro result.";
}

function calculationData<T>(response: ApiResponse<T>): T {
  if (!hasUsableData(response)) throw new Error(response.errors[0]?.message || "Macro calculation is unavailable. Review inputs or retry.");
  return response.data;
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
      serverFetchApiResponse<ProviderHealthRead[]>("/api/providers/health"),
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

    if (sic && (activeTab === "sector" || activeTab === "scenario")) {
      try {
        const sectorQuery = new URLSearchParams({ market, country, sic });
        const res = await serverFetchApiResponse<MacroSectorSensitivity>(`/api/valuation/macro/sector?${sectorQuery.toString()}`);
        sectorResult = calculationData(res);
        if (res.meta) metas.push(res.meta);
      } catch (error) {
        workbenchError = errorMessage(error);
      }
    }

    if (run === "configure") {
      try { macroPeriodCount(values.period_count); } catch (error) { workbenchError = errorMessage(error); }
    }

    if (run === "scenario") {
      try {
        if (!sic) throw new Error("Enter a SIC code before running a sector scenario.");
        const res = await serverPostApiResponse<MacroScenarioResult>("/api/valuation/macro/scenario", {
          market,
          country,
          sic_code: sic,
          rate_shock: macroNumber(values.rate_shock, "rate shock"),
          gdp_shock: macroNumber(values.gdp_shock, "GDP shock"),
          inflation_shock: macroNumber(values.inflation_shock, "inflation shock"),
          currency_shock: macroNumber(values.currency_shock, "currency shock"),
          currencyVariableDirection: stringParam(query, "currency_variable_direction") || null
        });
        scenarioResult = calculationData(res);
        if (res.meta) metas.push(res.meta);
      } catch (error) {
        workbenchError = errorMessage(error);
      }
    }

    if (run === "bottom-up") {
      try {
        const segments = macroBottomUpSegments(values);
        const res = await serverPostApiResponse<MacroSensitivityResult>("/api/valuation/macro/bottom-up", {
          market,
          country,
          segments: segments.map((segment) => ({
            name: segment.segment_name,
            sicCode: segment.sic_code,
            value: segment.segment_value,
          })),
        });
        bottomUpResult = calculationData(res);
        if (res.meta) metas.push(res.meta);
      } catch (error) {
        workbenchError = errorMessage(error);
      }
    }

    if (run === "top-down") {
      try {
        const periods = macroTopDownPeriods(values);
        const res = await serverPostApiResponse<MacroSensitivityResult>("/api/valuation/macro/top-down", {
          frequency: values.frequency || "annual",
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
        topDownResult = calculationData(res);
        if (res.meta) metas.push(res.meta);
      } catch (error) {
        workbenchError = errorMessage(error);
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
        <ClaimTypeBadges activeTab={activeTab} />
        <MacroLimitationsNotice />
        {workbenchError && activeTab !== "sector" ? <ErrorState message={workbenchError} /> : null}

        {activeTab === "sector" && <Panel title="Sector Sensitivity">
          <form className="form-grid" method="get">
            <input name="tab" type="hidden" value="sector" />
            <MarketControls country={country} market={market} sic={sic} />
            <div className="button-row">
              <button type="submit">Load Sector</button>
            </div>
          </form>
          {workbenchError && !sectorResult ? (
            <ErrorState message={workbenchError} />
          ) : null}
          {sectorResult ? <MacroSensitivityTable result={sectorResult} /> : !workbenchError ? <EmptyState label="Select a market and SIC to load real benchmark data." /> : null}
          {seriesListRes.meta ? <DataFreshnessIndicator meta={seriesListRes.meta} /> : null}
        </Panel>}

        {activeTab === "scenario" && <Panel title="Macro Shock Scenario">
          <MacroScenarioForm country={country} market={market} sic={sic} values={values} />
          {scenarioResult ? <ScenarioResult result={scenarioResult} /> : !workbenchError ? <EmptyState label="Run a scenario to estimate source-backed sector impact." /> : null}
        </Panel>}

        {activeTab === "bottom-up" && <Panel title="Bottom-Up Segment Sensitivity">
          <MacroBottomUpForm country={country} market={market} sic={sic} values={values} />
          {bottomUpResult ? <BottomUpResult result={bottomUpResult} /> : !workbenchError ? <EmptyState label="Enter one or more SIC-backed segments to calculate weighted exposure." /> : null}
        </Panel>}

        {activeTab === "top-down" && <Panel title="Top-Down Company History">
          <MacroTopDownForm country={country} market={market} sic={sic} values={values} />
          {topDownResult ? <TopDownResult result={topDownResult} /> : !workbenchError ? <EmptyState label="Enter at least three periods to estimate company-specific macro sensitivity." /> : null}
        </Panel>}

        {activeTab === "series" && <><Panel title="Import from FRED">
          {!hasUsableData(providerHealthRes) ? <ErrorState message="FRED configuration could not be checked. Reload to retry." /> : fredConfigured ? (
            <RetainedActionForm label="Import fred series" resetOnSuccess action={importFredSeries} className="form-grid">
              <TextField id="fred-import-series-id" label="FRED Series ID" name="series_id" placeholder="e.g. CPIAUCSL or FEDFUNDS" required />
              <div className="button-row" style={{ gridColumn: "1 / -1" }}>
                <button type="submit">Import Series & Observations</button>
              </div>
              <p className="text-sm text-gray-500 mt-2" style={{ gridColumn: "1 / -1" }}>
                Requires FRED API key. Use only for configured US macro series.
              </p>
            </RetainedActionForm>
          ) : (
            <NotConfiguredState
              title="FRED Integration Not Configured"
              description="Set FRED_API_KEY in your environment variables to import source-backed economic data directly from the Federal Reserve."
            />
          )}
        </Panel>

        <Panel title="Add Macro Series Manually">
          <RetainedActionForm label="Create macro series" resetOnSuccess action={createMacroSeries} className="form-grid">
            <TextField id="name" label="Series Name" name="name" placeholder="India 10Y Yield" required />
            <TextField id="units" label="Units" name="units" placeholder="%" />
            <TextField id="frequency" label="Frequency" name="frequency" placeholder="Monthly" />
            <TextAreaField className="field field-full" id="description" label="Description" name="description" />
            <div className="button-row">
              <button type="submit">Add Series</button>
            </div>
          </RetainedActionForm>
        </Panel>

        <Panel title="Add Observation">
          <RetainedActionForm label="Create macro observation" resetOnSuccess action={createMacroObservation} className="form-grid">
            <SelectField id="observation-series-id" label="Series" name="series_id" required>
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
          </RetainedActionForm>
        </Panel>

        <Panel title="Series & Data">
          {!hasUsableData(seriesListRes) ? <ErrorState message="Macro series could not be loaded. Reload to retry." /> : seriesList.length === 0 ? (
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
                    <div className="max-h-48 overflow-y-auto" role="region" aria-label={`${series.name} observations`} tabIndex={0}>
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
