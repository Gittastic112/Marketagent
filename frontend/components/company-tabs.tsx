"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useDataHealth } from "@/components/providers/data-health-provider";
import { AlertTriangle } from "lucide-react";


const tabDefinitions = [
  { segment: "", label: "Overview", sections: [""] },
  { segment: "fundamentals", label: "Financials", sections: ["fundamentals"] },
  { segment: "thesis", label: "Thesis", sections: ["thesis", "decisions"] },
  { segment: "valuation", label: "Valuation", sections: ["valuation"] },
  { segment: "filings", label: "Sources", sections: ["filings", "evidence"] },
] as const;

const relatedViews: Record<string, { segment: string; label: string }[]> = {
  thesis: [{ segment: "thesis", label: "Thesis" }, { segment: "decisions", label: "Decision journal" }],
  valuation: [{ segment: "valuation", label: "Models" }, { segment: "valuation/peers", label: "Peer comparisons" }],
  filings: [{ segment: "filings", label: "Filings" }, { segment: "evidence", label: "Evidence ledger" }],
};


export function CompanyTabs({ companyId }: { companyId: string }) {
  const pathname = usePathname();
  const base = `/companies/${companyId}`;
  const matches = (segment: string) => segment
    ? pathname === `${base}/${segment}` || pathname.startsWith(`${base}/${segment}/`)
    : pathname === base;
  const activeSegment = tabDefinitions.find(tab => tab.sections.some(matches))?.segment;
  const subviews = activeSegment ? relatedViews[activeSegment] || [] : [];
  const activeSubview = [...subviews].sort((a, b) => b.segment.length - a.segment.length).find(view => matches(view.segment));

  let staleSegments: Record<string, boolean> = {};
  try {
    const health = useDataHealth();
    staleSegments = health.staleSegments;
  } catch {
    // If not wrapped in provider, gracefully degrade
  }

  return (
    <div className="company-navigation">
    <div className="company-navigation-row">
    <nav className="company-tabs" aria-label="Company workspace">
      {tabDefinitions.map((tab) => {
        const href = tab.segment ? `${base}/${tab.segment}` : base;
        const active = tab.segment === activeSegment;
        return (
          <Link
            href={href}
            key={tab.label}
            prefetch={false}
            className={`${active ? "active" : ""} flex items-center gap-1.5`}
            aria-current={active ? "page" : undefined}
          >
            {tab.label}
            {tab.sections.some(segment => staleSegments[segment]) && (
              <span title="This section has stale data" aria-label="This section has stale data">
                <AlertTriangle className="text-[var(--warning)]" size={14} aria-hidden="true" />
              </span>
            )}
          </Link>
        );
      })}
    </nav>
    <details className="company-tools-menu">
      <summary className={matches("setup") ? "active" : undefined}>Company details</summary>
      <div className="company-tools-links">
        <Link prefetch={false} href={`${base}/setup`}>Identity and setup</Link>
        <Link prefetch={false} href={`${base}#company-tools`}>Exposure tags and filing intake</Link>
      </div>
    </details>
    </div>
    {subviews.length > 0 && <nav className="company-subviews" aria-label="Related company views">
      {subviews.map(view => <Link key={view.segment} href={`${base}/${view.segment}`} prefetch={false}
        aria-current={view === activeSubview ? "page" : undefined}>{view.label}</Link>)}
    </nav>}
    </div>
  );
}
