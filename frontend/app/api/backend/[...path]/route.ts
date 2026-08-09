import { getToken } from "next-auth/jwt";
import type { NextRequest } from "next/server";

import {
  createBackendAuthHeaders,
  INTERNAL_SIGNATURE_HEADER,
  INTERNAL_USER_HEADER,
} from "@/lib/internal-auth";

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
        source: "internal",
        last_updated: null,
        is_stale: true,
        is_mock: false,
        warnings: [],
        confidence: "none",
      },
      errors: [{ code, message }],
    },
    { status },
  );
}

async function proxyRequest(request: NextRequest, context: RouteContext) {
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
  const sourceUrl = new URL(request.url);
  const targetPath = path.map(encodeURIComponent).join("/");
  const targetUrl = `${API_BASE_URL}/${targetPath}${sourceUrl.search}`;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("cookie");
  headers.delete(INTERNAL_USER_HEADER);
  headers.delete(INTERNAL_SIGNATURE_HEADER);
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
      body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(),
      cache: "no-store",
      signal: AbortSignal.timeout(BACKEND_TIMEOUT_MS),
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  } catch (error) {
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
