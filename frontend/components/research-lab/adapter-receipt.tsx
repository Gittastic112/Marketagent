import Link from "next/link";

export function AdapterReceipt({ provider, runId, observedAt, status, documents, warnings, result }: {
  provider: string; runId: number | null; observedAt: string; status: string; documents: number[]; warnings: string[]; result: unknown;
}) {
  return <section className="research-run-result" aria-label="Adapter execution receipt">
    <h3>{provider} · {status.replaceAll("_", " ")}</h3>
    <p>Processing run {runId ?? "not available"} · Observed <time dateTime={observedAt}>{observedAt}</time>. Provider timestamps, coverage and price basis in the returned result remain authoritative; an observed time is not a live-data guarantee.</p>
    {!!warnings.length && <ul>{warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>}
    {!!documents.length && <div className="button-row">{documents.map(id => <Link key={id} prefetch={false} href={`/documents/${id}/sections`}>Inspect source document #{id}</Link>)}</div>}
    <p><Link href="/data-health" prefetch={false}>Open processing health and recent runs</Link></p>
    <pre className="research-json-result">{JSON.stringify(result, null, 2)}</pre>
  </section>;
}
