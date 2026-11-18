"use client";
// Temporary Mock Data browser harness. Removed before committing application changes.
import { useState } from "react";
import { ValuationMemoPanel } from "@/components/valuation/valuation-memo-panel";
import { PortfolioEvidenceImporter } from "@/components/portfolio/portfolio-evidence-importer";
import type { DcfAssumptionSet } from "@/lib/api/valuation";

export default function MockDataUiHarness() {
  const [version, setVersion] = useState(11);
  const [portfolio, setPortfolio] = useState(7);
  const assumptions = { id: version, scenario: "Base", updated_at: "2026-11-17T10:00:00Z", outputs: { id: version + 8 } } as DcfAssumptionSet;
  return <><h1>Mock Data UI verification</h1><p>Isolated response fixtures. No provider or stored user data is used.</p>
    <div className="button-row"><button type="button" onClick={() => setVersion(11)}>Version 11</button><button type="button" onClick={() => setVersion(12)}>Version 12</button>
      <button type="button" onClick={() => setPortfolio(7)}>Portfolio 7</button><button type="button" onClick={() => setPortfolio(8)}>Portfolio 8</button></div>
    <ValuationMemoPanel valuationId={7} assumptions={assumptions} blocked={false} />
    <PortfolioEvidenceImporter portfolioId={portfolio} />
  </>;
}
