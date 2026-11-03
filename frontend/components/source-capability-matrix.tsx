import type { SourceCapability, SourceCapabilityStatus } from "@/lib/api";

type CapabilityRow = {
  label: string;
  us: CapabilityCell;
  india: CapabilityCell;
};

type CapabilityCell = {
  status: SourceCapabilityStatus;
  provider: string;
  notes: string;
};

const STATUS_LABELS: Record<SourceCapabilityStatus, string> = {
  available: "Available",
  manual_only: "Manual only",
  not_configured: "Provider not configured",
  not_supported: "Not supported yet",
};

const STATUS_COLORS: Record<SourceCapabilityStatus, string> = {
  available: "var(--success)",
  manual_only: "var(--warning)",
  not_configured: "var(--text-secondary)",
  not_supported: "var(--error)",
};

function capabilityCell(
  capabilities: SourceCapability[],
  matcher: (capability: SourceCapability) => boolean,
  fallback: CapabilityCell,
): CapabilityCell {
  const capability = capabilities.find(matcher);
  if (!capability) {
    return fallback;
  }
  return {
    status: capability.status,
    provider: capability.provider_name,
    notes: capability.notes || fallback.notes,
  };
}

function manualCell(provider: string, notes: string): CapabilityCell {
  return { status: "manual_only", provider, notes };
}

function notConfiguredCell(provider: string, notes: string): CapabilityCell {
  return { status: "not_configured", provider, notes };
}

function marketPriceCell(capabilities: SourceCapability[]): CapabilityCell {
  return capabilityCell(
    capabilities,
    (capability) => capability.capability === "market_prices",
    notConfiguredCell("Selected price provider", "Price capability was not returned. Check Data Health and stored price coverage."),
  );
}

export function SourceCapabilityMatrix({
  usCapabilities,
  indiaCapabilities,
}: {
  usCapabilities: SourceCapability[];
  indiaCapabilities: SourceCapability[];
}) {
  const rows: CapabilityRow[] = [
    {
      label: "Company lookup",
      us: capabilityCell(usCapabilities, (capability) => capability.capability === "sec_filings",
        notConfiguredCell("SEC EDGAR", "SEC configuration was not returned by the backend.")),
      india: notConfiguredCell(
        "Local records",
        "India lookup returns existing local companies. Automated security master lookup is not configured.",
      ),
    },
    {
      label: "Filings and announcements",
      us: capabilityCell(
        usCapabilities,
        (capability) => capability.capability === "sec_filings",
        notConfiguredCell("SEC EDGAR", "SEC filing capability was not returned by the backend."),
      ),
      india: capabilityCell(
        indiaCapabilities,
        (capability) => capability.capability === "corporate_announcements",
        manualCell("NSE/BSE", "Automated India announcement ingestion is not enabled."),
      ),
    },
    {
      label: "Fundamentals",
      us: capabilityCell(
        usCapabilities,
        (capability) => capability.capability === "sec_fundamentals",
        notConfiguredCell("SEC EDGAR", "SEC fundamentals capability was not returned by the backend."),
      ),
      india: capabilityCell(
        indiaCapabilities,
        (capability) => capability.capability === "financial_statements",
        manualCell("Manual upload", "Use manual entries or imports until an India fundamentals provider is configured."),
      ),
    },
    {
      label: "Market prices",
      us: marketPriceCell(usCapabilities),
      india: marketPriceCell(indiaCapabilities),
    },
    {
      label: "Macro and rates",
      us: capabilityCell(usCapabilities, (capability) => capability.capability === "fred_macro",
        notConfiguredCell("FRED", "FRED capability was not returned. Manual macro context remains available.")),
      india: capabilityCell(
        indiaCapabilities,
        (capability) => capability.capability === "macro_sensitivity",
        manualCell("Manual context", "India macro sensitivity benchmarks exist, but risk-free rates are manual only."),
      ),
    },
    {
      label: "Valuation benchmarks",
      us: manualCell("Damodaran/local", "Use local benchmark tables and manual assumptions where a US row is absent."),
      india: capabilityCell(
        indiaCapabilities,
        (capability) => capability.capability === "damodaran_benchmarks",
        manualCell("Damodaran/local", "Imported benchmark files are expected but were not returned by the backend."),
      ),
    },
    {
      label: "Portfolio and manual entries",
      us: manualCell("Local database", "Holdings, transactions, prices, notes, and manual documents are supported locally."),
      india: manualCell("Local database", "Holdings, transactions, prices, notes, and manual documents are supported locally."),
    },
  ];

  return (
    <div tabIndex={0} className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Capability</th>
            <th>United States</th>
            <th>India</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <td>
                <strong>{row.label}</strong>
              </td>
              <CapabilityStatusCell cell={row.us} />
              <CapabilityStatusCell cell={row.india} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CapabilityStatusCell({ cell }: { cell: CapabilityCell }) {
  const color = STATUS_COLORS[cell.status];
  return (
    <td>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
        <span className="badge" style={{ backgroundColor: "var(--surface-muted)", border: `1px solid ${color}`, color }}>
          {STATUS_LABELS[cell.status]}
        </span>
        <span style={{ color: "var(--text-primary)", fontSize: "0.9rem" }}>{cell.provider}</span>
        <span style={{ color: "var(--text-secondary)", fontSize: "0.82rem", lineHeight: 1.4 }}>{cell.notes}</span>
      </div>
    </td>
  );
}
