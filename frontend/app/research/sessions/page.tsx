"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader, Panel, ErrorState, EmptyState } from "@/components/page";
import api from "@/lib/api";

export default function SessionsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    api.get("/research/sessions")
      .then((res: any) => { setSessions(res.data as any[] || []); setLoading(false); })
      .catch((err: any) => { setError(err.message); setLoading(false); });
  }, []);

  const createSession = async () => {
    setCreateError(null);
    try {
      const title = `Research Session ${new Date().toLocaleDateString()}`;
      const res: any = await api.post("/research/sessions", { title });
      if (res.data?.id) router.push(`/research/sessions/${res.data.id}`);
    } catch (err: any) {
      setCreateError(err.message || "Failed to create the research session.");
    }
  };

  if (loading) return <div style={{ padding: "2rem" }}>Loading sessions...</div>;
  if (error) return <ErrorState message={error} />;

  return (
    <>
      <PageHeader eyebrow="AI Analysis" title="Research Sessions" />
      <div style={{ marginBottom: "2rem" }}>
        <button onClick={createSession} className="primary-button">Start New Session</button>
        {createError ? <p className="inline-error" role="alert">{createError}</p> : null}
      </div>

      <div className="metric-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1.5rem" }}>
        {sessions.length === 0 ? (
          <EmptyState label="No sessions found." />
        ) : (
          sessions.map(session => (
            <Panel key={session.id} title={session.title}>
              <p className="muted">Created: {new Date(session.created_at).toLocaleDateString()}</p>
              <div style={{ marginTop: "1rem" }}>
                <button onClick={() => router.push(`/research/sessions/${session.id}`)} className="secondary-button">
                  Continue
                </button>
              </div>
            </Panel>
          ))
        )}
      </div>
    </>
  );
}
