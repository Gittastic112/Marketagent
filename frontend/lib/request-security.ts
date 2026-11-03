/** Local browser boundary. Never trust forwarded-host/origin headers. */
export const MAX_PROXY_BODY_BYTES = 42 * 1024 * 1024;

export function trustedBrowserOrigin(headers: Headers, configuredUrl: string): string | null {
  try {
    const configured = new URL(configuredUrl);
    const origins = [configured];
    if (["localhost", "127.0.0.1"].includes(configured.hostname)) {
      const alias = new URL(configured);
      alias.hostname = configured.hostname === "localhost" ? "127.0.0.1" : "localhost";
      origins.push(alias);
    }
    return origins.find(origin => origin.host === headers.get("host"))?.origin ?? null;
  } catch { return null; }
}

export function isSameOriginMutation(headers: Headers, configuredUrl: string): boolean {
  const trusted = trustedBrowserOrigin(headers, configuredUrl);
  return trusted !== null && headers.get("origin") === trusted
    && headers.get("sec-fetch-site") !== "cross-site";
}

export function backendRequestHeaders(incoming: Headers): Headers {
  const result = new Headers();
  for (const name of ["content-type", "accept", "x-request-id"]) {
    const value = incoming.get(name);
    if (value) result.set(name, value);
  }
  return result;
}

export async function readBoundedBody(request: Request, maxBytes = MAX_PROXY_BODY_BYTES): Promise<ArrayBuffer> {
  const declared = request.headers.get("content-length");
  if (declared !== null && (!/^\d{1,12}$/.test(declared) || Number(declared) > maxBytes)) {
    throw new RangeError("Request body exceeds the 42 MiB limit");
  }
  if (!request.body) return new ArrayBuffer(0);
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new Error("UPLOAD_TIMEOUT")), 30_000);
  });
  try {
    while (true) {
      const { done, value } = await Promise.race([reader.read(), deadline]);
      if (done) break;
      total += value.byteLength;
      if (total > maxBytes) throw new RangeError("Request body exceeds the 42 MiB limit");
      chunks.push(value);
    }
    const body = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
    return body.buffer;
  } finally {
    clearTimeout(timer);
    void reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
