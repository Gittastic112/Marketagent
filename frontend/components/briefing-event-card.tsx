import React from 'react';

interface BriefingEventCardProps {
    event_id: number;
    headline: string;
    priority?: string;
    ticker?: string;
    form_type?: string;
    status?: 'New' | 'Unresolved' | 'Stale' | 'Reviewed';
}

export function BriefingEventCard({ event_id, headline, priority, ticker, form_type, status = 'New' }: BriefingEventCardProps) {
    return (
        <article className="brief-item">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <h3 style={{ margin: 0 }}>{ticker ? `${ticker} - ` : ''}{headline}</h3>
                <span className="badge" style={{ backgroundColor: 'var(--surface-sunken)', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>{status}</span>
            </div>

            <div className="meta-row" style={{ display: 'flex', gap: '8px', fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px' }}>
                {priority && <span>Priority: {priority}</span>}
                {form_type && <span>Form: {form_type}</span>}
            </div>

            <div className="button-row">
                <a href={`/events/${event_id}`} style={{ padding: '6px 12px', border: '1px solid var(--border)', borderRadius: '4px', textDecoration: 'none', color: 'var(--text)', fontSize: '14px' }}>
                    View Source Evidence
                </a>
            </div>
        </article>
    );
}
