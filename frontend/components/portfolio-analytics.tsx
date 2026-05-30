import { PortfolioAnalytics } from "@/lib/api";

function formatMoney(value: number | null, currency: string) {
  if (value === null) return "-";
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(value);
}

function formatPercent(value: number | null) {
  if (value === null) return "-";
  return new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 2 }).format(value / 100);
}

export function PortfolioAnalyticsDashboard({ analytics }: { analytics: PortfolioAnalytics }) {
  return (
    <div className="analytics-dashboard" style={{ display: 'flex', flexDirection: 'column', gap: '2rem', marginBottom: '2rem' }}>
      
      {analytics.diversification_warnings.length > 0 && (
        <div style={{ backgroundColor: 'var(--color-red-50)', color: 'var(--color-red-900)', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--color-red-200)' }}>
          <h4 style={{ margin: '0 0 0.5rem 0' }}>⚠️ Diversification Warnings</h4>
          <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
            {analytics.diversification_warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div style={{ padding: '1.5rem', border: '1px solid var(--color-gray-200)', borderRadius: '0.5rem', backgroundColor: 'var(--color-white)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)', marginBottom: '0.5rem' }}>Total Portfolio Value</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{formatMoney(analytics.total_portfolio_value, analytics.base_currency)}</div>
        </div>
        <div style={{ padding: '1.5rem', border: '1px solid var(--color-gray-200)', borderRadius: '0.5rem', backgroundColor: 'var(--color-white)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)', marginBottom: '0.5rem' }}>Total Invested</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{formatMoney(analytics.total_invested_value, analytics.base_currency)}</div>
        </div>
        <div style={{ padding: '1.5rem', border: '1px solid var(--color-gray-200)', borderRadius: '0.5rem', backgroundColor: 'var(--color-white)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)', marginBottom: '0.5rem' }}>Total Cash</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{formatMoney(analytics.total_cash_value, analytics.base_currency)}</div>
        </div>
        <div style={{ padding: '1.5rem', border: '1px solid var(--color-gray-200)', borderRadius: '0.5rem', backgroundColor: 'var(--color-white)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)', marginBottom: '0.5rem' }}>Unrealized P&L</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600, color: (analytics.total_unrealized_pnl || 0) >= 0 ? 'var(--color-green-700)' : 'var(--color-red-700)' }}>
            {formatMoney(analytics.total_unrealized_pnl, analytics.base_currency)}
            {analytics.total_unrealized_pnl_percent != null && <div style={{ fontSize: '1rem', marginTop: '0.25rem' }}>{formatPercent(analytics.total_unrealized_pnl_percent)}</div>}
          </div>
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
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Sector</th>
                  <th>Weight</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(analytics.sector_exposure).sort((a,b) => b[1] - a[1]).map(([sector, weight]) => (
                  <tr key={sector}>
                    <td>{sector}</td>
                    <td>{formatPercent(weight)}</td>
                  </tr>
                ))}
                {Object.keys(analytics.sector_exposure).length === 0 && <tr><td colSpan={2}>No sectors found.</td></tr>}
              </tbody>
            </table>
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
                    <td style={{ color: 'var(--color-green-700)' }}>
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
                    <td style={{ color: 'var(--color-red-700)' }}>
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
