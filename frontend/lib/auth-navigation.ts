/** Return only a local destination, including after URL normalization. */
export function localCallback(value: string | null, origin: string): string {
  if (!value || /[\\\x00-\x20]/.test(value)) return "/";
  try {
    const base = new URL(origin);
    const target = new URL(value, base.origin);
    const decodedPath = decodeURIComponent(target.pathname);
    if (target.origin !== base.origin || target.username || target.password
        || decodedPath.startsWith("//") || decodedPath.includes("\\")) return "/";
    return `${target.pathname}${target.search}${target.hash}`;
  } catch {
    return "/";
  }
}
