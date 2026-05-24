"use client";

import { useEffect } from "react";

const DEBUG_LOGS_ENABLED = process.env.NEXT_PUBLIC_DEBUG_LOGS !== "false";

export function BrowserDebugLogger() {
  useEffect(() => {
    if (DEBUG_LOGS_ENABLED) {
      console.log("[browser] Market Intelligence frontend mounted", {
        apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000",
        href: window.location.href
      });
    }
  }, []);

  return null;
}
