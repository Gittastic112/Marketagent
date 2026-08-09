"use client";

import { useState } from "react";
import { fetchLatestMarketPrice } from "@/lib/api";

export function SyncPriceButton({ companyId, market }: { companyId: number, market: string | null }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSync = async () => {
    setLoading(true);
    setError(null);
    try {
      await fetchLatestMarketPrice(companyId);
      window.location.reload();
    } catch (err: any) {
      setError(err.message || "Failed to sync price");
      setLoading(false);
    }
  };

  // Currently supporting India for explicit yfinance integration per Phase 15.
  // We can show it for others too if yfinance works globally.
  return (
    <div className="flex flex-col gap-1 items-start">
      <button
        onClick={handleSync}
        disabled={loading}
        className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded border border-gray-300 disabled:opacity-50"
      >
        {loading ? "Syncing..." : "Sync Latest Price"}
      </button>
      {error && <span className="text-red-500 text-xs">{error}</span>}
    </div>
  );
}
