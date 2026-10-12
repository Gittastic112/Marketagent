/** A stored citation is an external link, never executable content. No fetching. */
export function sourceLink(value: string | null | undefined): string | null {
  if (!value || /[\u0000-\u0020\u007f\\]/.test(value)) return null;
  try {
    const parsed = new URL(value);
    if (!["https:", "http:"].includes(parsed.protocol) || parsed.username || parsed.password) return null;
    return value;
  } catch {
    return null;
  }
}
