/** Slow explicit generation gets time for provider completion and durable writes. */
export function backendTimeoutMs(method: string, path: string): number {
  if (method === "POST" && (/^research\/sessions\/\d+\/messages$/.test(path)
    || /^brief-sources\/\d+\/analyze$/.test(path))) return 60_000;
  return 15_000;
}
