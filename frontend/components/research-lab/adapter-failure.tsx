import Link from "next/link";
import { ApiError } from "@/lib/api/contract";

export function AdapterFailure({ error }: { error: Error | null }) {
  if (!error) return null;
  const runId = error instanceof ApiError ? error.processingRunId : undefined;
  return <div role="alert">
    <p>{error.message}</p>
    {runId && <p>Processing run #{runId} records this attempt. <Link href="/data-health" prefetch={false}>Open processing history</Link></p>}
  </div>;
}
