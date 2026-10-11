import "server-only";

import { connection } from "next/server";

import { ApiError, errorResponse, type ApiResponse } from "@/lib/api/contract";
import { createBackendAuthHeaders } from "@/lib/internal-auth";
import { readServerIdentity } from "@/lib/server-auth";

const SERVER_API_TIMEOUT_MS = 15_000;

type ParsedServerResponse<T> = {
  response: Response;
  body: ApiResponse<T> | { detail?: string } | T | null;
};

async function authenticatedBackendHeaders(secret: string | undefined): Promise<Record<string, string>> {
  if (!secret) {
    throw new ApiError("AUTH_NOT_CONFIGURED", 503);
  }

  const identity = await readServerIdentity(secret);
  if (!identity) {
    throw new ApiError("NOT_AUTHENTICATED", 401);
  }
  return createBackendAuthHeaders(identity, secret);
}

async function serverResponse<T>(
  method: string,
  path: string,
  payload?: unknown,
  timeoutMs = SERVER_API_TIMEOUT_MS,
): Promise<ParsedServerResponse<T>> {
  await connection();
  const secret = process.env["NEXTAUTH_SECRET"];
  const apiBaseUrl = process.env["API_BASE_URL"]
    ?? process.env["NEXT_PUBLIC_API_BASE_URL"]
    ?? "http://127.0.0.1:8000";
  const authHeaders = await authenticatedBackendHeaders(secret);
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    cache: "no-store",
    redirect: "error",
    headers: {
      ...authHeaders,
      ...(payload === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: payload === undefined ? undefined : JSON.stringify(payload),
    signal: AbortSignal.timeout(timeoutMs),
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

async function serverApiResponse<T>(
  method: string,
  path: string,
  payload?: unknown,
  options?: { timeoutMs?: number },
): Promise<ApiResponse<T>> {
  try {
    const { response, body } = await serverResponse<T>(method, path, payload, options?.timeoutMs);
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
    if (error instanceof ApiError && error.message === "AUTH_NOT_CONFIGURED") {
      return errorResponse<T>(error.message, "Local authentication is not configured.");
    }
    if (error instanceof ApiError && error.message === "NOT_AUTHENTICATED") {
      return errorResponse<T>(error.message, "The local session is missing or expired. Sign in again.");
    }
    const message = error instanceof Error ? error.message : "Network request failed";
    return errorResponse<T>("NETWORK_ERROR", message);
  }
}

export async function serverFetchApiResponse<T>(
  path: string,
  options?: { timeoutMs?: number },
): Promise<ApiResponse<T>> {
  return serverApiResponse<T>("GET", path, undefined, options);
}

export async function serverPostApi<T>(path: string, payload: unknown): Promise<T> {
  const res = await serverRequest<T>("POST", path, payload);
  return res.data as T;
}

export async function serverPostApiResponse<T>(path: string, payload: unknown): Promise<ApiResponse<T>> {
  return serverApiResponse<T>("POST", path, payload);
}

export async function serverPatchApi<T>(path: string, payload: unknown): Promise<T> {
  const res = await serverRequest<T>("PATCH", path, payload);
  return res.data as T;
}

export async function serverPutApi<T>(path: string, payload: unknown): Promise<T> {
  const res = await serverRequest<T>("PUT", path, payload);
  return res.data as T;
}

export async function serverDeleteApi<T>(path: string): Promise<T> {
  const res = await serverRequest<T>("DELETE", path);
  return res.data as T;
}
