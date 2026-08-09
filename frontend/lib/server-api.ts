import "server-only";

import { cache } from "react";
import { getServerSession } from "next-auth";

import { ApiError, type ApiResponse } from "@/lib/api";
import { authOptions } from "@/lib/auth-options";
import { createBackendAuthHeaders } from "@/lib/internal-auth";

const SERVER_API_BASE_URL =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const SERVER_API_TIMEOUT_MS = 15_000;

type SessionIdentity = {
  id?: string;
  email?: string | null;
  name?: string | null;
};

type ParsedServerResponse<T> = {
  response: Response;
  body: ApiResponse<T> | { detail?: string } | T | null;
};

function errorResponse<T>(code: string, message: string, status = "error"): ApiResponse<T> {
  return {
    data: null,
    meta: {
      status,
      last_updated: null,
      source: "internal",
      is_stale: true,
      warnings: [],
      confidence: "none",
      processing_time_ms: null,
    },
    errors: [{ code, message }],
  };
}

const authenticatedBackendHeaders = cache(async (): Promise<Record<string, string>> => {
  const secret = process.env.NEXTAUTH_SECRET;
  if (!secret) {
    throw new ApiError("AUTH_NOT_CONFIGURED", 503);
  }

  const session = await getServerSession(authOptions);
  const user = session?.user as SessionIdentity | undefined;
  if (!user?.id) {
    throw new ApiError("NOT_AUTHENTICATED", 401);
  }
  return createBackendAuthHeaders({
    id: user.id,
    email: user.email,
    name: user.name,
  });
});

async function serverResponse<T>(method: string, path: string, payload?: unknown): Promise<ParsedServerResponse<T>> {
  const authHeaders = await authenticatedBackendHeaders();
  const response = await fetch(`${SERVER_API_BASE_URL}${path}`, {
    method,
    cache: "no-store",
    headers: {
      ...authHeaders,
      ...(payload === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: payload === undefined ? undefined : JSON.stringify(payload),
    signal: AbortSignal.timeout(SERVER_API_TIMEOUT_MS),
  });

  const body = await response.json().catch(() => null) as ApiResponse<T> | { detail?: string } | null;
  return { response, body };
}

async function serverRequest<T>(method: string, path: string, payload?: unknown): Promise<ApiResponse<T>> {
  const { response, body } = await serverResponse<T>(method, path, payload);
  const objectBody = body !== null && typeof body === "object" ? body : null;
  if (!response.ok) {
    const envelopeError = objectBody && "errors" in objectBody ? (objectBody as any).errors?.[0]?.message : undefined;
    const detail = objectBody && "detail" in objectBody ? (objectBody as any).detail : undefined;
    throw new ApiError(envelopeError || detail || `API request failed: ${response.status}`, response.status);
  }
  if (objectBody && "meta" in objectBody && "errors" in objectBody) {
    const envelope = objectBody as ApiResponse<T>;
    if (envelope.errors?.length) {
      throw new ApiError(envelope.errors[0].message, response.status);
    }
    return envelope;
  }
  return {
    data: body as T,
    meta: {
      status: "success",
      last_updated: null,
      source: "internal",
      is_stale: false,
      warnings: ["Legacy API response did not include metadata."],
      confidence: "unknown",
      processing_time_ms: null,
    },
    errors: [],
  };
}

export async function serverFetchApi<T>(path: string): Promise<T> {
  const res = await serverRequest<T>("GET", path);
  return res.data as T;
}

export async function serverFetchApiResponse<T>(path: string): Promise<ApiResponse<T>> {
  try {
    const { response, body } = await serverResponse<T>("GET", path);
    if (body && typeof body === "object" && "meta" in body && "errors" in body) {
      return body as ApiResponse<T>;
    }
    if (!response.ok) {
      const detail = body && typeof body === "object" && "detail" in body ? body.detail : undefined;
      return errorResponse<T>("API_ERROR", detail || `API request failed: ${response.status}`);
    }
    return {
      data: body as T,
      meta: {
        status: "success",
        last_updated: null,
        source: "internal",
        is_stale: false,
        warnings: ["Legacy API response did not include metadata."],
        confidence: "unknown",
        processing_time_ms: null,
      },
      errors: [],
    };
  } catch (error) {
    if (error instanceof ApiError && (error.message === "AUTH_NOT_CONFIGURED" || error.message === "NOT_AUTHENTICATED")) {
      return errorResponse<T>(error.message, "Authentication error");
    }
    const message = error instanceof Error ? error.message : "Network request failed";
    return errorResponse<T>("NETWORK_ERROR", message);
  }
}

export async function serverPostApi<T>(path: string, payload: unknown): Promise<T> {
  const res = await serverRequest<T>("POST", path, payload);
  return res.data as T;
}

export async function serverPostApiResponse<T>(path: string, payload: unknown): Promise<ApiResponse<T>> {
  try {
    const { response, body } = await serverResponse<T>("POST", path, payload);
    if (body && typeof body === "object" && "meta" in body && "errors" in body) {
      return body as ApiResponse<T>;
    }
    if (!response.ok) {
      const detail = body && typeof body === "object" && "detail" in body ? body.detail : undefined;
      return errorResponse<T>("API_ERROR", detail || `API request failed: ${response.status}`);
    }
    return {
      data: body as T,
      meta: {
        status: "success",
        last_updated: null,
        source: "internal",
        is_stale: false,
        warnings: ["Legacy API response did not include metadata."],
        confidence: "unknown",
        processing_time_ms: null,
      },
      errors: [],
    };
  } catch (error) {
    if (error instanceof ApiError && (error.message === "AUTH_NOT_CONFIGURED" || error.message === "NOT_AUTHENTICATED")) {
      return errorResponse<T>(error.message, "Authentication error");
    }
    const message = error instanceof Error ? error.message : "Network request failed";
    return errorResponse<T>("NETWORK_ERROR", message);
  }
}

export async function serverPatchApi<T>(path: string, payload: unknown): Promise<T> {
  const res = await serverRequest<T>("PATCH", path, payload);
  return res.data as T;
}

export async function serverDeleteApi<T>(path: string): Promise<T> {
  const res = await serverRequest<T>("DELETE", path);
  return res.data as T;
}
