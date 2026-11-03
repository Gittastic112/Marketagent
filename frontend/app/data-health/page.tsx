import { receiptAuditCursor } from "@/lib/peer-health-navigation";
import { ErrorState, PageHeader } from "@/components/page";
import { loadDataHealth, type HealthAuditMode } from "@/lib/server/data-health";
import { HealthOverview } from "@/components/data-health/health-overview";

export const dynamic = "force-dynamic";

export default async function DataHealthPage({ searchParams }: { searchParams: Promise<{ audit?: string; peer_after?: string | string[]; }>; }) {
  const { audit, peer_after } = await searchParams;
  const peerAfter = receiptAuditCursor(peer_after);
  const auditMode: HealthAuditMode = audit === "evidence" || audit === "coverage" || audit === "backfill" ? audit : null;
  try {
    const data = await loadDataHealth(auditMode, peerAfter);
    return <HealthOverview {...data} />;
  } catch {
    return (
      <>
        <PageHeader eyebrow="System Health" title="Data Health" />
        <ErrorState message="Could not load data health information from the backend." />
      </>
    );
  }
}
