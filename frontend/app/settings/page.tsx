import { updateScoringConfig } from "@/app/actions";
import { TextField } from "@/components/form-fields";
import { PageHeader, Panel } from "@/components/page";
import { CsvUploadForm } from "@/components/csv-upload-form";
import { fetchApi, fetchOAuthStatus } from "@/lib/api";
import type { ScoringConfig, TokenStatusResponse } from "@/lib/api";

export default async function SettingsPage() {
  const config = await fetchApi<ScoringConfig>("/scoring-config");
  
  // Fetch OAuth status, handle potential 500 if ENCRYPTION_KEY is missing
  let oauthStatus: TokenStatusResponse[] = [];
  let encryptionError = false;
  try {
    oauthStatus = await fetchOAuthStatus();
  } catch (e) {
    encryptionError = true;
  }

  return (
    <>
      <PageHeader eyebrow="System configuration" title="Settings" />

      <Panel title="Integrations & Security">
        <p className="text-sm text-gray-500 mb-4">
          Manage secure connections to external providers. 
          Broker sync is planned for a future phase once this foundation is fully verified.
        </p>
        
        {encryptionError ? (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
            <p className="text-sm text-red-700">
              <strong>Encryption Key Missing:</strong> The <code>ENCRYPTION_KEY</code> environment variable is not set. 
              Tokens cannot be securely encrypted. Please generate a key and add it to your <code>.env</code> file.
            </p>
          </div>
        ) : (
          <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4">
            <p className="text-sm text-green-700">
              <strong>Secure Storage Active:</strong> Symmetric encryption is configured and active.
            </p>
          </div>
        )}

        <div className="flex flex-col gap-3">
          {oauthStatus.length === 0 && !encryptionError && (
             <p className="text-sm text-gray-500 italic">No providers connected yet.</p>
          )}
          {oauthStatus.map((status) => (
             <div key={status.provider_name} className="flex justify-between items-center border p-3 rounded">
               <div>
                 <p className="font-medium text-sm text-gray-900">{status.provider_name}</p>
                 <p className="text-xs text-gray-500">
                   {status.is_connected ? "Connected" : "Disconnected"}
                   {status.expires_at ? ` · Expires: ${new Date(status.expires_at).toLocaleDateString()}` : ""}
                 </p>
               </div>
               <button className="button secondary-button text-xs" disabled>
                 Manage
               </button>
             </div>
          ))}
        </div>
      </Panel>

      <Panel title="Scoring Weights">
        <p className="text-sm text-gray-500 mb-4">
          Adjust the relative weights used to calculate the Priority Score of an event. These weights must be decimals (e.g., 0.35).
        </p>
        <form action={updateScoringConfig} className="form-grid">
          <TextField
            id="weight_credibility"
            label="Credibility Weight"
            name="weight_credibility"
            type="number"
            step="0.01"
            defaultValue={config.weight_credibility.toString()}
            required
          />
          <TextField
            id="weight_novelty"
            label="Novelty Weight"
            name="weight_novelty"
            type="number"
            step="0.01"
            defaultValue={config.weight_novelty.toString()}
            required
          />
          <TextField
            id="weight_impact"
            label="Impact Weight"
            name="weight_impact"
            type="number"
            step="0.01"
            defaultValue={config.weight_impact.toString()}
            required
          />
          <TextField
            id="weight_speed"
            label="Speed Bonus Weight"
            name="weight_speed"
            type="number"
            step="0.01"
            defaultValue={config.weight_speed.toString()}
            required
          />
          <div className="button-row">
            <button type="submit">Save Settings</button>
          </div>
        </form>
      </Panel>

      <Panel title="Data Export">
        <p className="text-sm text-gray-500 mb-4">
          Download your data in CSV format for local backup or analysis.
        </p>
        <div className="flex flex-col gap-3">
          <a href="/api/backend/export/portfolio-holdings" target="_blank" rel="noopener noreferrer" className="button secondary-button w-fit text-sm">
            Export Portfolio Holdings
          </a>
          <a href="/api/backend/export/portfolio-transactions" target="_blank" rel="noopener noreferrer" className="button secondary-button w-fit text-sm">
            Export Portfolio Transactions
          </a>
          <a href="/api/backend/export/market-prices" target="_blank" rel="noopener noreferrer" className="button secondary-button w-fit text-sm">
            Export Market Prices
          </a>
          <a href="/api/backend/export/raw-documents" target="_blank" rel="noopener noreferrer" className="button secondary-button w-fit text-sm">
            Export Raw Documents
          </a>
          <a href="/api/backend/export/events" target="_blank" rel="noopener noreferrer" className="button secondary-button w-fit text-sm">
            Export Events
          </a>
        </div>
      </Panel>

      <Panel title="Data Import">
        <p className="text-sm text-gray-500 mb-4">
          Upload CSV files to import data. Note: The imported data format must precisely match the exported CSV format.
        </p>
        <div className="flex flex-col gap-3">
          <CsvUploadForm endpoint="/import/portfolio-holdings" label="Import Portfolio Holdings" />
          <CsvUploadForm endpoint="/import/portfolio-transactions" label="Import Portfolio Transactions" />
          <CsvUploadForm endpoint="/import/market-prices" label="Import Market Prices" />
        </div>
      </Panel>
    </>
  );
}
