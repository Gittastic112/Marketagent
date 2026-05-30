import { CompanyMarketData } from "@/lib/api";

export function CompanyMarketHeader({ data }: { data: CompanyMarketData | null }) {
  if (!data) return null;
  
  const isPositive = (data.change_percent ?? 0) >= 0;
  const changeColor = isPositive ? "text-green-600" : "text-red-600";
  
  return (
    <div className="flex gap-6 mt-3 items-end">
      <div className="flex items-end gap-2">
        <span className="text-3xl font-bold tracking-tight">
          {data.current_price ? `$${data.current_price.toFixed(2)}` : "—"}
        </span>
        {data.change_percent !== null && (
          <span className={`text-lg font-medium mb-1 ${changeColor}`}>
            {isPositive ? "+" : ""}{data.change_percent.toFixed(2)}%
          </span>
        )}
      </div>
      {data.market_cap && (
        <div className="text-sm text-[var(--color-neutral-500)] mb-1">
          <span className="font-medium mr-1">Mkt Cap:</span>
          {(data.market_cap / 1e9).toFixed(2)}B
        </div>
      )}
      {data.pe_ratio && (
        <div className="text-sm text-[var(--color-neutral-500)] mb-1">
          <span className="font-medium mr-1">P/E:</span>
          {data.pe_ratio.toFixed(2)}
        </div>
      )}
    </div>
  );
}
