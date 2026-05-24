import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  status
}: {
  eyebrow: string;
  title: string;
  status?: string;
}) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {status ? <div className="status">{status}</div> : null}
    </header>
  );
}

export function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

export function EmptyState({ label }: { label: string }) {
  return <div className="empty">{label}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="error">{message}</div>;
}
