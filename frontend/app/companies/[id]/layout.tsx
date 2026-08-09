import type { ReactNode } from "react";

import { CompanyTabs } from "@/components/company-tabs";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company } from "@/lib/api";
import { StaleDataBanner, MockDataState } from "@/components/ui/data-states";
import { DataHealthProvider } from "@/components/providers/data-health-provider";


export default async function CompanyLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let isStale = false;
  let isMock = false;
  try {
    const res = await serverFetchApiResponse<Company>(`/companies/${id}`);
    isStale = !!res.meta?.is_stale;
    isMock = !!res.meta?.is_mock || res.meta?.source === "mock";
  } catch (err) {
    // Ignore errors here; page components will handle 404s
  }

  return (
    <DataHealthProvider>
      <div className="company-workspace">
        {isStale && <StaleDataBanner message="Showing cached company data because backend is unreachable." />}
        {isMock && <MockDataState message="Company data is mocked. Treat values as placeholders." />}
        <CompanyTabs companyId={id} />
        {children}
      </div>
    </DataHealthProvider>
  );
}
