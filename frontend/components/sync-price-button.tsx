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
    <div className="sync-price-control">
      <button
        onClick={handleSync}
        disabled={loading}
        className="secondary-button"
      >
        {loading ? "Syncing..." : "Sync Latest Price"}
      </button>
      {error && <span className="inline-error">{error}</span>}
    </div>
  );
}
