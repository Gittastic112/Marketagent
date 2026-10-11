import Link from "next/link";
import { notFound } from "next/navigation";
import { ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import { PeerSetWorkspace } from "@/components/valuation/peer-set-workspace";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, PeerValuationSet } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CompanyPeersPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const companyId = Number(id);
  if (!/^\d+$/.test(id) || !Number.isSafeInteger(companyId) || companyId < 1) notFound();
  const [company, sets] = await Promise.all([
    serverFetchApiResponse<Company>(`/companies/${companyId}`),
    serverFetchApiResponse<PeerValuationSet[]>(`/api/valuation/relative/peer-sets?company_id=${companyId}&include_archived=true`),
  ]);
  return <>
    <PageHeader eyebrow={company.data?.ticker ?? "Company peer evidence"} title="Comparable companies" />
    <Link prefetch={false} href={`/companies/${companyId}/valuation`}>Back to valuation models</Link>
    <DataStateNotices metas={[company.meta, sets.meta]} />
    <Panel title="Source evidence and diagnostic review">
      <p>Manage peer evidence and review diagnostics before using a set in relative valuation. A DCF model is not required to manage peers.</p>
      {!company.data ? <ErrorState message="Company could not be loaded." errors={company.errors} />
        : !sets.data ? <ErrorState message="Peer sets could not be loaded. Reload to retry." errors={sets.errors} />
        : <PeerSetWorkspace companyId={companyId} initialSets={sets.data} />}
    </Panel>
  </>;
}
