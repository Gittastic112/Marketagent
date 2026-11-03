"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { ErrorState, EmptyState } from "@/components/page";
import { fetchResearchSession, sendResearchMessage, type ResearchSession } from "@/lib/api/research";
import { AI_DISCLOSURES } from "@/lib/ai-privacy";
import { createRequestGate } from "@/lib/latest-request";
import { AiOutputMetadata } from "@/components/ai-metadata";
import { AiOutputReviewControls } from "@/components/ai-output-review-controls";

export default function SessionDetailPage() {
  const params = useParams();
  return <SessionWorkspace key={String(params.id)} sessionId={String(params.id)} />;
}

function SessionWorkspace({sessionId}: {sessionId: string}) {
  const router = useRouter();
  const [session, setSession] = useState<ResearchSession | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [privacyAcknowledged, setPrivacyAcknowledged] = useState(false);
  const [lastResponseWasMock, setLastResponseWasMock] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const reads = useMemo(createRequestGate, []);
  const writes = useMemo(createRequestGate, []);
  const busy = useRef(false);

  const fetchSession = async () => {
    const current = reads.begin();
    setError(null);
    try {
      const data = await fetchResearchSession(sessionId);
      if (!current()) return null;
      setSession(data);
      return data;
    } catch (err) {
      if (current()) {setSession(null); setError(err instanceof Error ? err.message : "Session unavailable");}
      return null;
    } finally {
      if (current()) setLoading(false);
    }
  };

  useEffect(() => {
    if (sessionId) fetchSession();
    return () => {reads.invalidate(); writes.invalidate();};
  }, [sessionId]);

  useEffect(() => {
    if (session?.messages?.length) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [session?.messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || busy.current || !privacyAcknowledged || !session) return;

    const content = input.trim();
    const current = writes.begin();
    const knownIds = new Set(session.messages.map(message => message.id));
    busy.current = true;
    setSending(true);
    setSendError(null);

    try {
      const response = await sendResearchMessage(sessionId, content);
      if (!current()) return;
      setLastResponseWasMock(Boolean(response.ai_output?.is_mock));
      setInput("");
      await fetchSession();
    } catch (err) {
      if (!current()) return;
      const refreshed = await fetchSession();
      if (!current()) return;
      const confirmed = refreshed?.messages.some(message => !knownIds.has(message.id)
        && message.role === "user" && message.content === content);
      if (confirmed) setInput("");
      setSendError(`${err instanceof Error ? err.message : "The AI response failed."} ${confirmed
        ? "Your research message was saved without an assistant response."
        : "Save could not be confirmed. Your text is retained. Inspect the session before retrying to avoid duplicates."}`);
    } finally {
      busy.current = false;
      if (current()) setSending(false);
    }
  };

  if (loading) return <div role="status" style={{ padding: "2rem" }}>Loading session...</div>;
  if (error || !session) return <><ErrorState message={error || "Session unavailable"} /><button type="button" onClick={() => void fetchSession()}>Reload session</button></>;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 4rem)" }}>
      <div style={{ padding: "1.5rem", borderBottom: "1px solid var(--border-color)", display: "flex", alignItems: "center", gap: "1rem" }}>
        <button onClick={() => router.push("/research/sessions")} aria-label="Back to research sessions" className="secondary-button" style={{ padding: "0.5rem" }}>
          ←
        </button>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.75rem", fontWeight: 600 }}>{session.title}</h1>
          <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>Source-backed AI Research</p>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {(!session.messages || session.messages.length === 0) ? (
          <EmptyState label="No messages yet. Start the research session by asking a question." />
        ) : (
          session.messages.map((msg) => (
            <div id={`message-${msg.id}`} key={msg.id} className="anchored-record" style={{ display: "flex", gap: "1rem", flexDirection: msg.role === "user" ? "row-reverse" : "row" }}>
              <div id={msg.ai_output ? `ai-output-${msg.ai_output.id}` : undefined} style={{
                width: "2rem", height: "2rem", borderRadius: "50%",
                backgroundColor: msg.role === "user" ? "var(--accent-color)" : "var(--bg-secondary)",
                display: "flex", alignItems: "center", justifyContent: "center",
                color: msg.role === "user" ? "white" : "inherit"
              }}>
                {msg.role === "user" ? "U" : "AI"}
              </div>
              <div style={{
                maxWidth: "70%", padding: "1rem", borderRadius: "0.5rem",
                backgroundColor: msg.role === "user" ? "var(--accent-color)" : "var(--bg-secondary)",
                color: msg.role === "user" ? "white" : "inherit"
              }}>
                <p style={{ margin: 0, whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{msg.content}</p>
                {msg.ai_output && <AiOutputMetadata aiOutput={msg.ai_output} />}
                {msg.ai_output && <AiOutputReviewControls initialOutput={msg.ai_output} />}
                <div style={{ fontSize: "var(--font-size-xs)", marginTop: "0.5rem", opacity: 0.7, textAlign: msg.role === "user" ? "right" : "left" }}>
                  {new Date(msg.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{ padding: "1.5rem", borderTop: "1px solid var(--border-color)", backgroundColor: "var(--bg-primary)" }}>
        {lastResponseWasMock && (
          <p style={{ margin: "0 0 0.75rem", color: "var(--warning-color)", fontSize: "0.85rem" }}>
            Mock Data: the last assistant response was deterministic demo or test output.
          </p>
        )}
        {sendError ? <p className="inline-error" role="alert">{sendError}</p> : null}
        {sending && <p role="status">Sending research message. Waiting for saved-message confirmation.</p>}
        <label style={{ display: "flex", gap: "0.5rem", alignItems: "flex-start", marginBottom: "0.75rem", fontSize: "0.85rem" }}>
          <input
            type="checkbox"
            checked={privacyAcknowledged}
            onChange={(event) => setPrivacyAcknowledged(event.target.checked)}
          />
          <span>{AI_DISCLOSURES.researchChat}</span>
        </label>
        <form onSubmit={sendMessage} style={{ display: "flex", gap: "0.5rem" }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about companies, events, or market trends..."
            aria-label="Research question"
            style={{
              flex: 1, minWidth: 0, padding: "0.75rem 1rem", borderRadius: "0.5rem",
              border: "1px solid var(--border-color)", backgroundColor: "var(--bg-secondary)"
            }}
            disabled={sending}
          />
          <button
            type="submit"
            className="primary-button"
            disabled={!input.trim() || sending || !privacyAcknowledged}
            style={{ padding: "0.75rem", display: "flex", alignItems: "center", justifyContent: "center" }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
