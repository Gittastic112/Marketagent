import { PageHeader, ErrorState } from "@/components/page";
import type { Company } from "@/lib/api";
import { serverFetchApiResponse } from "@/lib/server-api";
import { QuickValuationWorkflow } from "@/components/quick-valuation-workflow";
import { MockDataState, StaleDataBanner } from "@/components/ui/data-states";

export default async function QuickValuationPage() {
  try {
    const companiesRes = await serverFetchApiResponse<Company[]>("/companies");
    const companies = companiesRes.data || [];
    const isStale = companiesRes.meta?.is_stale;
    const isMock = companiesRes.meta?.is_mock || companiesRes.meta?.source === "mock";

    return (
      <>
        <PageHeader eyebrow="Valuation & DCF" title="Quick Valuation Workflow" />

        {isStale && <StaleDataBanner message="Showing cached company data because backend is unreachable." />}
        {isMock && <MockDataState message="Company list is mock data. Do not use them as live market coverage." />}

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
