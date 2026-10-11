import { EvaluationWorkspace } from "@/components/evaluation-workspace";
import { ErrorState, PageHeader } from "@/components/page";
import type { EvaluationRun } from "@/lib/api/evaluation";
import { serverFetchApi } from "@/lib/server-api";

export default async function EvaluationsPage() {
  const runs = await serverFetchApi<EvaluationRun[]>("/evaluations/runs").catch(() => null);
  return <>
    <PageHeader eyebrow="Research quality" title="Evaluations" />
    {runs === null ? <ErrorState message="Evaluation history is unavailable. Restore backend/schema readiness and reload; no cached results are shown." />
      : <EvaluationWorkspace initialRuns={runs} />}
  </>;
}
