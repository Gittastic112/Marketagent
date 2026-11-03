import { PageHeader, ErrorState } from "@/components/page";
import type { Company } from "@/lib/api";
import { serverFetchApiResponse } from "@/lib/server-api";
import { QuickValuationWorkflow } from "@/components/quick-valuation-workflow";
import { DataStateNotices } from "@/components/ui/data-states";

export default async function QuickValuationPage() {
  try {
    const companiesRes = await serverFetchApiResponse<Company[]>("/companies");
    const companies = companiesRes.data || [];

    return (
      <>
        <PageHeader eyebrow="Valuation & DCF" title="Quick Valuation Workflow" />

        <DataStateNotices
          metas={[companiesRes.meta]}
          mockMessage="Company list is mock data. Do not use them as live market coverage."
        />

        <QuickValuationWorkflow companies={companies} />
      </>
    );
  } catch (error) {
    return (
      <>
        <PageHeader eyebrow="Valuation & DCF" title="Quick Valuation Workflow" />
        <ErrorState message="Could not load companies. Ensure backend is running." />
      </>
    );
  }
}
