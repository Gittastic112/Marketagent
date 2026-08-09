"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useDataHealth } from "@/components/providers/data-health-provider";
import { AlertTriangle } from "lucide-react";


const tabDefinitions = [
  { segment: "", label: "Overview" },
  { segment: "setup", label: "Setup" },
  { segment: "filings", label: "Filings" },
  { segment: "fundamentals", label: "Fundamentals" },
  { segment: "thesis", label: "Thesis" },
  { segment: "decisions", label: "Decisions" },
  { segment: "valuation", label: "Valuation" },
  { segment: "evidence", label: "Evidence" },
] as const;


export function CompanyTabs({ companyId }: { companyId: string }) {
  const pathname = usePathname();
  const base = `/companies/${companyId}`;

  let staleSegments: Record<string, boolean> = {};
  try {
    const health = useDataHealth();
    staleSegments = health.staleSegments;
  } catch {
    // If not wrapped in provider, gracefully degrade
  }

  return (
    <nav className="company-tabs" aria-label="Company workspace">
      {tabDefinitions.map((tab) => {
        const href = tab.segment ? `${base}/${tab.segment}` : base;
        const active = tab.segment
          ? pathname === href || pathname.startsWith(`${href}/`)
          : pathname === base;
        return (
          <Link
            href={href}
            key={tab.label}
            prefetch={false}
            className={`${active ? "active" : ""} flex items-center gap-1.5`}
            aria-current={active ? "page" : undefined}
          >
            {tab.label}
            {staleSegments[tab.segment] && (
              <span title="This section has stale data" aria-label="This section has stale data">
                <AlertTriangle className="text-amber-500" size={14} aria-hidden="true" />
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
