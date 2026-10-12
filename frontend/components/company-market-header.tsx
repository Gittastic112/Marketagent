import type { ApiResponse } from "@/lib/api/contract";
import type { CompanyMarketData } from "@/lib/api/market";
import { DataStateNotices, ErrorState } from "@/components/ui/data-states";
import { formatNumber } from "@/lib/formatting";

export function CompanyMarketHeader({ response }: { response: ApiResponse<CompanyMarketData> }) {
  if (response.errors.length || response.meta.status !== "success") {
    return <div><ErrorState message="Price data could not be loaded." errors={response.errors} />
      <a href="/data-health">Check price provider health</a></div>;
  }
  const data = response.data;
  if (!data) return <div role="status"><p>No stored quote for this company.</p>
    <a href="/data-health">Check price provider health</a></div>;

  const currency = data.currency?.trim() || "Currency unknown";
  const hasPrice = data.current_price !== null && Number.isFinite(data.current_price);
  const hasChange = data.change_percent !== null && Number.isFinite(data.change_percent);
  const isPositive = (data.change_percent ?? 0) >= 0;

  return (
    <div style={{ minWidth: 0 }} aria-label="Stored market quote">
      <DataStateNotices metas={[response.meta]} mockMessage="This stored quote is Mock Data." />
      <div className="company-market-data">
      <div className="company-market-price">
        <span>{hasPrice ? `${currency} ${formatNumber(data.current_price)}` : "Price not available"}</span>
        {hasChange && <span className={isPositive ? "is-positive" : "is-negative"}>
          {isPositive ? "+" : ""}{data.change_percent!.toFixed(2)}%
        </span>}
      </div>
      {data.market_cap !== null && Number.isFinite(data.market_cap) && (
        <div className="company-market-stat"><strong>Market cap</strong>
          {currency} {new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(data.market_cap)}
        </div>
      )}
      {data.pe_ratio !== null && Number.isFinite(data.pe_ratio) && (
        <div className="company-market-stat"><strong>P/E</strong>{formatNumber(data.pe_ratio)}</div>
      )}
      </div>
      <details><summary>Quote source and timing</summary>
      <p className="muted">Stored quote · Source: {data.provider_name || "Unknown"}
        {data.provider_symbol ? ` (${data.provider_symbol})` : ""} · {data.price_type || "Price type unknown"}.</p>
      <p className="muted">Source timestamp: {data.source_timestamp || "Unknown"}.
        {" "}Observed: {data.observed_at || "Unknown"}. Stored update: {data.last_updated || "Unknown"}.</p>
      <p className="muted">{data.delay_minutes == null ? "Delay unknown" : `Reported delay: ${data.delay_minutes} minutes`}.
        {" "}A stored quote is not a verified current price or final close.</p>
      {!!data.warnings?.length && <ul className="compact-list">{data.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>}
      </details>
    </div>
  );
}
