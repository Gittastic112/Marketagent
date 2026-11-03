import { getToken } from "next-auth/jwt";
import type { NextRequest } from "next/server";

import {
  createBackendAuthHeaders,
} from "@/lib/internal-auth";
import { backendRequestHeaders, isSameOriginMutation, readBoundedBody, trustedBrowserOrigin } from "@/lib/request-security";

const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const BACKEND_TIMEOUT_MS = 15_000;

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

function proxyError(status: number, code: string, message: string): Response {
  return Response.json(
    {
      data: null,
      meta: {
        status: "error",
        source: "transport",
        last_updated: null,
        is_stale: false,
        is_mock: false,
        warnings: [message],
        confidence: "none",
      },
      errors: [{ code, message }],
    },
    { status, headers: { "Cache-Control": "private, no-store" } },
  );
}

async function proxyRequest(request: NextRequest, context: RouteContext) {
  const configuredUrl = process.env.NEXTAUTH_URL ?? "http://localhost:3000";
  if (!trustedBrowserOrigin(request.headers, configuredUrl)) {
    return proxyError(403, "UNTRUSTED_HOST", "This host is not allowed");
  }
  if (!["GET", "HEAD"].includes(request.method) && !isSameOriginMutation(request.headers, configuredUrl)) {
    return proxyError(403, "UNTRUSTED_ORIGIN", "This action must come from the app's own page");
  }
  const secret = process.env.NEXTAUTH_SECRET;
  if (!secret) {
    return proxyError(503, "AUTH_NOT_CONFIGURED", "Authentication is not configured");
  }

  const token = await getToken({ req: request, secret });
  const userId = typeof token?.id === "string" ? token.id : token?.sub;
  if (!userId) {
    return proxyError(401, "NOT_AUTHENTICATED", "Not authenticated");
  }

  const { path } = await context.params;
  if (path.some(part => part === "." || part === ".." || /[/\\\x00-\x1f]/.test(part))) {
    return proxyError(400, "INVALID_PATH", "Invalid backend path");
  }
  const sourceUrl = new URL(request.url);
  const targetPath = path.map(encodeURIComponent).join("/");
  // Explicit AI scans allow the provider's bounded 30-second call plus validation.
  // Ordinary navigation keeps its short timeout.
  const timeoutMs = request.method === "POST" && /^brief-sources\/\d+\/analyze$/.test(targetPath)
    ? 45_000 : BACKEND_TIMEOUT_MS;
  const targetUrl = `${API_BASE_URL}/${targetPath}${sourceUrl.search}`;
  const headers = backendRequestHeaders(request.headers);
  const authHeaders = createBackendAuthHeaders(
    {
      id: userId,
      email: typeof token?.email === "string" ? token.email : null,
      name: typeof token?.name === "string" ? token.name : null,
    },
    secret,
  );
  for (const [name, value] of Object.entries(authHeaders)) {
    headers.set(name, value);
  }

  try {
    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body: request.method === "GET" || request.method === "HEAD" ? undefined : await readBoundedBody(request),
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(timeoutMs),
    });

    const responseHeaders = new Headers(response.headers);
    for (const name of ["set-cookie", "connection", "transfer-encoding", "content-encoding", "content-length"]) responseHeaders.delete(name);
    responseHeaders.set("Cache-Control", "private, no-store");
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    if (error instanceof RangeError) return proxyError(413, "REQUEST_TOO_LARGE", error.message);
    if (error instanceof Error && error.message === "UPLOAD_TIMEOUT") return proxyError(408, "UPLOAD_TIMEOUT", "Upload timed out. Try again.");
    const timedOut = error instanceof Error && error.name === "TimeoutError";
    return proxyError(
      timedOut ? 504 : 502,
      timedOut ? "BACKEND_TIMEOUT" : "BACKEND_UNAVAILABLE",
      timedOut ? "The backend request timed out" : "The backend is unavailable",
    );
  }
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}
