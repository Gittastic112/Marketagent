/** Budget explicit work separately from navigation, status reads and downloads. */
export function backendTimeoutMs(method: string, path: string): number {
  if (method !== "POST") return 15_000;

  // Research workers have 40 seconds, followed by receipt persistence.
  if (/^api\/research-lab\/(allocation|simulation|report|peers)$/.test(path)
    || /^research\/sessions\/\d+\/messages$/.test(path)
    || /^brief-sources\/\d+\/analyze$/.test(path)) return 60_000;

  // Extraction can take 60 seconds after fetching the source. Remote adapters
  // can also make multiple bounded calls before saving a single audit receipt.
  if (/^api\/companies\/\d+\/source-adapters\/(sec-facts|transcript|documents\/\d+\/extract)$/.test(path)
    || path === "api/source-adapters/fred-vintage") return 120_000;

  // The market workflow itself allows 120 seconds before recording its outcome.
  if (/^api\/data-adapters\/(fmp|massive|nse_mcp)\/(quote|history|dated-quote|corporate-actions|reference)$/.test(path)
    || path === "api/data-adapters/identity/openfigi"
    || path === "api/data-adapters/calendars/schedule") return 150_000;

  return 15_000;
}
