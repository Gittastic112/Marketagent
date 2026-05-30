import { createMacroSeries, createMacroObservation, deleteMacroSeriesWithState, importFredSeries } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { MacroSeries } from "@/lib/api";

export default async function MacroPage() {
  try {
    const seriesList = await fetchApi<MacroSeries[]>("/macro");

    return (
      <>
        <PageHeader eyebrow="Economic Data" title="Macro Series" status={`${seriesList.length} series`} />
        
        <Panel title="Import from FRED">
          <form action={importFredSeries} className="form-grid">
            <TextField id="series_id" label="FRED Series ID" name="series_id" placeholder="e.g. CPIAUCSL or FEDFUNDS" required />
            <div className="button-row" style={{ gridColumn: "1 / -1" }}>
              <button type="submit">Import Series & Observations</button>
            </div>
            <p className="text-sm text-gray-500 mt-2" style={{ gridColumn: "1 / -1" }}>
              Note: Requires FRED API Key to be configured in your environment variables.
            </p>
          </form>
        </Panel>

        <Panel title="Add Macro Series Manually">
          <form action={createMacroSeries} className="form-grid">
            <TextField id="name" label="Series Name" name="name" placeholder="US CPI YoY" required />
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
                    <span>Units: {series.units || 'N/A'}</span>
                    <span>Freq: {series.frequency || 'N/A'}</span>
                  </div>
                  
                  <h4 className="text-sm font-medium mb-2 border-b pb-1">Observations</h4>
                  {series.observations.length === 0 ? (
                    <p className="text-sm text-gray-500">No data points yet.</p>
                  ) : (
                    <div className="max-h-48 overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-gray-500">
                            <th className="font-normal pb-1">Date</th>
                            <th className="font-normal pb-1 text-right">Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {/* Sort descending by date */}
                          {[...series.observations].sort((a, b) => new Date(b.date_recorded).getTime() - new Date(a.date_recorded).getTime()).map(obs => (
                            <tr key={obs.id} className="border-t border-gray-100">
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
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Economic Data" title="Macro Series" />
        <ErrorState message="Could not load macro data from the backend API." />
      </>
    );
  }
}
