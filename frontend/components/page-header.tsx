import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  eyebrow?: string;
  status?: string;
  children?: ReactNode;
}

export function PageHeader({ title, eyebrow, status, children }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {status && <div className="status" style={{ marginTop: '12px', display: 'inline-block' }}>{status}</div>}
      </div>
      {children && (
        <div className="page-header-actions">
          {children}
        </div>
      )}
    </header>
  );
}
