import Link from "next/link";
import { BriefSourceTriage } from "@/components/brief-source-triage";
import { ErrorState, PageHeader } from "@/components/page";
import type { Company } from "@/lib/api/companies";
import { serverFetchApiResponse } from "@/lib/server-api";

export default async function BriefTriagePage({ searchParams }: { searchParams: Promise<{ company_id?: string }> }) {
  const [response, params] = await Promise.all([serverFetchApiResponse<Company[]>("/companies"), searchParams]);
  const requested = Number(params.company_id);
  const selected = response.data?.find(company => company.id === requested)?.id ?? null;
  return <>
    <PageHeader eyebrow="Private research" title="Compare input evidence" status="Evidence-linked review" />
    <p>See how stored AI findings relate to the same valuation input. Compare exact passages, source dates and opposing suggestions before deciding what deserves a closer look.</p>
    <div className="section-intro"><Link href="/daily-brief" prefetch={false}>← Research inbox</Link></div>
    {response.data ? <BriefSourceTriage key={selected ?? "unselected"} companies={response.data} initialCompanyId={selected} />
      : <ErrorState message="Company selection is unavailable. Reload this page to retry." errors={response.errors} />}
  </>;
}
