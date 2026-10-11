import type { ReactNode } from "react";

import { CompanyTabs } from "@/components/company-tabs";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { ApiMeta, Company } from "@/lib/api";
import { DataStateNotices } from "@/components/ui/data-states";
import { DataHealthProvider } from "@/components/providers/data-health-provider";


export default async function CompanyLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let companyMeta: ApiMeta | null = null;
  try {
    const res = await serverFetchApiResponse<Company>(`/companies/${id}`);
    companyMeta = res.meta;
  } catch (err) {
    // Ignore errors here; page components will handle 404s
  }

  return (
    <DataHealthProvider>
      <div className="company-workspace">
        <DataStateNotices
          metas={[companyMeta]}
          mockMessage="Company data is mocked. Treat values as placeholders."
        />
        <CompanyTabs companyId={id} />
        {children}
      </div>
    </DataHealthProvider>
  );
}
