"use client";

import { PortfolioAnalytics } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from "recharts";

function formatMoney(value: number | null, currency: string) {
  if (value === null) return "-";
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(value);
}

function formatPercent(value: number | null) {
  if (value === null) return "-";
  return new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 2 }).format(value / 100);
}

export function PortfolioAnalyticsDashboard({ analytics, snapshots = [] }: { analytics: PortfolioAnalytics, snapshots?: any[] }) {
  const chartData = snapshots.map(s => ({
    date: s.snapshot_date,
    value: s.total_market_value != null ? Number(s.total_market_value) : 0
  })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  const sectorData = Object.entries(analytics.sector_exposure).map(([sector, weight]) => ({
    name: sector,
    weight: weight
  })).sort((a, b) => b.weight - a.weight);

  return (
    <div className="analytics-dashboard" style={{ display: 'flex', flexDirection: 'column', gap: '2rem', marginBottom: '2rem' }}>

      {analytics.diversification_warnings.length > 0 && (
        <div style={{ backgroundColor: 'var(--danger-bg)', color: 'var(--danger)', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--danger)' }}>
          <h4 style={{ margin: '0 0 0.5rem 0' }}>⚠️ Diversification Warnings</h4>
          <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
            {analytics.diversification_warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      {chartData.length > 1 && (
        <div style={{ height: 300, padding: '1.5rem', borderRadius: '0.5rem', backgroundColor: 'var(--surface)', border: '1px solid var(--line)' }}>
          <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem', color: 'var(--text)' }}>Historical Performance</h3>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--line)" />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: 'var(--muted)' }} tickLine={false} axisLine={false} />
              <YAxis
                tickFormatter={(val) => new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(val)}
                tick={{ fontSize: 12, fill: 'var(--muted)' }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                formatter={(value: number) => formatMoney(value, analytics.base_currency)}
                contentStyle={{ borderRadius: '8px', border: '1px solid var(--line)', backgroundColor: 'var(--surface)' }}
              />
              <Line type="monotone" dataKey="value" stroke="var(--accent)" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div style={{ padding: '1.5rem', border: '1px solid var(--line)', borderRadius: '0.5rem', backgroundColor: 'var(--surface)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>Total Portfolio Value</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{formatMoney(analytics.total_portfolio_value, analytics.base_currency)}</div>
        </div>
        <div style={{ padding: '1.5rem', border: '1px solid var(--line)', borderRadius: '0.5rem', backgroundColor: 'var(--surface)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>Total Invested</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{formatMoney(analytics.total_invested_value, analytics.base_currency)}</div>
        </div>
        <div style={{ padding: '1.5rem', border: '1px solid var(--line)', borderRadius: '0.5rem', backgroundColor: 'var(--surface)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>Total Cash</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{formatMoney(analytics.total_cash_value, analytics.base_currency)}</div>
        </div>
        <div style={{ padding: '1.5rem', border: '1px solid var(--line)', borderRadius: '0.5rem', backgroundColor: 'var(--surface)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>Unrealized P&L</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600, color: (analytics.total_unrealized_pnl || 0) >= 0 ? 'var(--success)' : 'var(--danger)' }}>
            {formatMoney(analytics.total_unrealized_pnl, analytics.base_currency)}
            {analytics.total_unrealized_pnl_percent != null && <div style={{ fontSize: '1rem', marginTop: '0.25rem' }}>{formatPercent(analytics.total_unrealized_pnl_percent)}</div>}
          </div>
        </div>
        <div style={{ padding: '1.5rem', border: '1px solid var(--line)', borderRadius: '0.5rem', backgroundColor: 'var(--surface)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>FX Impact</div>
          {analytics.fx_impact != null ? (
            <div style={{ fontSize: '1.5rem', fontWeight: 600, color: analytics.fx_impact >= 0 ? 'var(--success)' : 'var(--danger)' }}>
              {formatMoney(analytics.fx_impact, analytics.base_currency)}
            </div>
          ) : (
            <div style={{ fontSize: '1.25rem', fontWeight: 500, color: 'var(--muted)', fontStyle: 'italic' }}>Not Configured</div>
          )}
        </div>
        <div style={{ padding: '1.5rem', border: '1px solid var(--line)', borderRadius: '0.5rem', backgroundColor: 'var(--surface)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>Opportunity Cost</div>
          {analytics.opportunity_cost != null ? (
            <div style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text)' }}>
              {formatMoney(analytics.opportunity_cost, analytics.base_currency)}
              {analytics.opportunity_cost_percent != null && <div style={{ fontSize: '1rem', marginTop: '0.25rem', color: 'var(--muted)' }}>{formatPercent(analytics.opportunity_cost_percent)} vs benchmark</div>}
            </div>
          ) : (
            <div style={{ fontSize: '1.25rem', fontWeight: 500, color: 'var(--muted)', fontStyle: 'italic' }}>Not Configured</div>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div>
          <h3>Top Positions</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Weight</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {analytics.top_positions.map((p) => (
                  <tr key={p.holding_id}>
                    <td><strong>{p.ticker}</strong></td>
                    <td>{formatPercent(p.weight_percent)}</td>
                    <td>{formatMoney(p.market_value, p.currency)}</td>
                  </tr>
                ))}
                {analytics.top_positions.length === 0 && <tr><td colSpan={3}>No positions.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3>Sector Exposure</h3>
          <div style={{ height: 250, padding: '1rem', border: '1px solid var(--line)', borderRadius: '0.5rem', backgroundColor: 'var(--surface)' }}>
            {sectorData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sectorData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)" />
                  <XAxis type="number" tickFormatter={(val) => formatPercent(val)} tick={{ fontSize: 12, fill: 'var(--muted)' }} />
                  <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12, fill: 'var(--muted)' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    formatter={(value: number) => formatPercent(value)}
                    contentStyle={{ borderRadius: '8px', border: '1px solid var(--line)', backgroundColor: 'var(--surface)' }}
                  />
                  <Bar dataKey="weight" fill="var(--accent)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ color: 'var(--muted)', textAlign: 'center', marginTop: '2rem' }}>No sector data found.</div>
            )}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div>
          <h3>Top Gainers</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Unrealized P&L</th>
                </tr>
              </thead>
              <tbody>
                {analytics.top_gainers.map((p) => (
                  <tr key={p.holding_id}>
                    <td><strong>{p.ticker}</strong></td>
                    <td style={{ color: 'var(--success)' }}>
                      {formatMoney(p.unrealized_pnl, p.currency)}
                      {p.unrealized_pnl_percent != null && ` (${formatPercent(p.unrealized_pnl_percent)})`}
                    </td>
                  </tr>
                ))}
                {analytics.top_gainers.length === 0 && <tr><td colSpan={2}>No gainers.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3>Top Losers</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Unrealized P&L</th>
                </tr>
              </thead>
              <tbody>
                {analytics.top_losers.map((p) => (
                  <tr key={p.holding_id}>
                    <td><strong>{p.ticker}</strong></td>
                    <td style={{ color: 'var(--danger)' }}>
                      {formatMoney(p.unrealized_pnl, p.currency)}
                      {p.unrealized_pnl_percent != null && ` (${formatPercent(p.unrealized_pnl_percent)})`}
                    </td>
                  </tr>
                ))}
                {analytics.top_losers.length === 0 && <tr><td colSpan={2}>No losers.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>
  );
}
