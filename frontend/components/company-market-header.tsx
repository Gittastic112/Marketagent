import { CompanyMarketData } from "@/lib/api";

export function CompanyMarketHeader({ data }: { data: CompanyMarketData | null }) {
  if (!data) return null;
  
  const isPositive = (data.change_percent ?? 0) >= 0;
  const changeClass = isPositive ? "is-positive" : "is-negative";
  
  return (
    <div className="company-market-data">
      <div className="company-market-price">
        <span>
          {data.current_price ? `$${data.current_price.toFixed(2)}` : "—"}
        </span>
        {data.change_percent !== null && (
          <span className={changeClass}>
            {isPositive ? "+" : ""}{data.change_percent.toFixed(2)}%
          </span>
        )}
      </div>
      {data.market_cap && (
        <div className="company-market-stat">
          <strong>Market cap</strong>
          {(data.market_cap / 1e9).toFixed(2)}B
        </div>
      )}
      {data.pe_ratio && (
        <div className="company-market-stat">
          <strong>P/E</strong>
          {data.pe_ratio.toFixed(2)}
        </div>
      )}
    </div>
  );
}
