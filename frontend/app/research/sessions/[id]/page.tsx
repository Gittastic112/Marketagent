"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { PageHeader, ErrorState, EmptyState } from "@/components/page";
import api from "@/lib/api";
import { Send, User, Bot, ArrowLeft } from "lucide-react";

export default function SessionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [session, setSession] = useState<any>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sessionId = params.id as string;

  const fetchSession = async () => {
    try {
      const res = await api.get(`/research/sessions/${sessionId}`);
      setSession(res.data);
    } catch (err: any) {
      setError(err.message || "Failed to load session");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sessionId) fetchSession();
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const content = input.trim();
    setInput("");
    setSending(true);

    // Optimistic update
    const tempMsg = { id: Date.now(), role: "user", content, created_at: new Date().toISOString() };
    setSession((prev: any) => ({ ...prev, messages: [...(prev.messages || []), tempMsg] }));

    try {
      // Send user message
      await api.post(`/research/sessions/${sessionId}/messages`, { role: "user", content });
      
      // Send mock AI response (since we don't have a real AI integration yet)
      const aiResponse = "I am an AI assistant analyzing the market data based on your request. (Mock Response)";
      await api.post(`/research/sessions/${sessionId}/messages`, { role: "assistant", content: aiResponse });
      
      // Refresh to get actual messages
      await fetchSession();
    } catch (err: any) {
      alert("Failed to send message: " + err.message);
      // Revert optimistic update by refetching
      await fetchSession();
    } finally {
      setSending(false);
    }
  };

  if (loading) return <div style={{ padding: "2rem" }}>Loading session...</div>;
  if (error || !session) return <ErrorState message={error || "Session not found"} />;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 4rem)" }}>
      <div style={{ padding: "1.5rem", borderBottom: "1px solid var(--border-color)", display: "flex", alignItems: "center", gap: "1rem" }}>
        <button onClick={() => router.push("/research/sessions")} className="secondary-button" style={{ padding: "0.5rem" }}>
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 600 }}>{session.title}</h1>
          <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>Source-backed AI Research</p>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {(!session.messages || session.messages.length === 0) ? (
          <EmptyState label="No messages yet. Start the research session by asking a question." />
        ) : (
          session.messages.map((msg: any) => (
            <div key={msg.id} style={{ display: "flex", gap: "1rem", flexDirection: msg.role === "user" ? "row-reverse" : "row" }}>
              <div style={{ 
                width: "2rem", height: "2rem", borderRadius: "50%", 
                backgroundColor: msg.role === "user" ? "var(--accent-color)" : "var(--bg-secondary)",
                display: "flex", alignItems: "center", justifyContent: "center",
                color: msg.role === "user" ? "white" : "inherit"
              }}>
                {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>
              <div style={{ 
                maxWidth: "70%", padding: "1rem", borderRadius: "0.5rem",
                backgroundColor: msg.role === "user" ? "var(--accent-color)" : "var(--bg-secondary)",
                color: msg.role === "user" ? "white" : "inherit"
              }}>
                <p style={{ margin: 0, whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{msg.content}</p>
                <div style={{ fontSize: "0.7rem", marginTop: "0.5rem", opacity: 0.7, textAlign: msg.role === "user" ? "right" : "left" }}>
                  {new Date(msg.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{ padding: "1.5rem", borderTop: "1px solid var(--border-color)", backgroundColor: "var(--bg-primary)" }}>
        <form onSubmit={sendMessage} style={{ display: "flex", gap: "0.5rem" }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about companies, events, or market trends..."
            style={{ 
              flex: 1, padding: "0.75rem 1rem", borderRadius: "0.5rem", 
              border: "1px solid var(--border-color)", backgroundColor: "var(--bg-secondary)" 
            }}
            disabled={sending}
          />
          <button 
            type="submit" 
            className="primary-button" 
            disabled={!input.trim() || sending}
            style={{ padding: "0.75rem", display: "flex", alignItems: "center", justifyContent: "center" }}
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
