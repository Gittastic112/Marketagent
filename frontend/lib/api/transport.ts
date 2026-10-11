/** HTTP transport only. Domain endpoints belong in sibling modules. */
import { ApiError, errorResponse } from "./contract.ts";
import type { ApiResponse } from "./contract.ts";

const SERVER_API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const BROWSER_API_BASE_URL = process.env.NEXT_PUBLIC_BROWSER_API_BASE_URL ?? "/api/backend";

const DEBUG_LOGS_ENABLED = process.env.NEXT_PUBLIC_DEBUG_LOGS === "true";

function getApiBaseUrl(): string {
  return typeof window === "undefined" ? SERVER_API_BASE_URL : BROWSER_API_BASE_URL;
}

function logApiStart(method: string, path: string) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} -> ${getApiBaseUrl()}${path}`);
  }
}

function logApiSuccess(method: string, path: string, status: number) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} succeeded with ${status}`);
  }
}

function logApiFailure(method: string, path: string, status: number) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} failed with ${status}`);
  }
}

async function apiError(response: Response): Promise<ApiError> {
  try {
    const body = await response.json();
    if (body && Array.isArray(body.errors) && body.errors.length > 0) {
      return new ApiError(body.errors[0].message, response.status);
    }
    if (body && typeof body.detail === "string") {
      return new ApiError(body.detail, response.status);
    }
  } catch {
    // Fall back to the generic message below when the response body is not JSON.
  }
  return new ApiError(`API request failed: ${response.status}`, response.status);
}

async function parseApiResponse<T>(response: Response): Promise<T> {
  const payload = await response.json();

  if (payload && typeof payload === "object" && "meta" in payload) {
    const apiResponse = payload as ApiResponse<T>;
    if (apiResponse.errors && apiResponse.errors.length > 0) {
      throw new ApiError(apiResponse.errors[0].message, response.status);
    }
    return apiResponse.data as T;
  }

  return payload as T;
}

export async function fetchApi<T>(path: string): Promise<T> {
  return parseApiResponse<T>(await checkedRequest("GET", path, { cache: "no-store" }));
}

export async function fetchApiResponse<T>(path: string): Promise<ApiResponse<T>> {
  logApiStart("GET", path);
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      cache: "no-store"
    });
  } catch (e: any) {
    logApiFailure("GET", path, 0);
    return errorResponse<T>("NETWORK_ERROR", `Network request failed: ${e.message}`);
  }

  if (!response.ok) {
    logApiFailure("GET", path, response.status);
    // Even if it's an error, try to parse it as an ApiResponse to get the structured errors.
    try {
      const payload = await response.json() as ApiResponse<T>;
      if (payload.meta && payload.errors) {
        return payload;
      }
    } catch {
      // Fallback if not JSON or doesn't match format
    }

    // Return a synthetic ApiResponse for network/generic errors
    return errorResponse<T>("NETWORK_ERROR", `API request failed: ${response.status}`);
  }

  logApiSuccess("GET", path, response.status);
  try {
    return await response.json() as ApiResponse<T>;
  } catch {
    return errorResponse<T>("PARSE_ERROR", "Failed to parse API response");
  }
}

async function checkedRequest(method: string, path: string, init: RequestInit, allowNotFound = false): Promise<Response> {
  logApiStart(method, path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, init);
  if (allowNotFound && response.status === 404) return response;
  if (!response.ok) {
    logApiFailure(method, path, response.status);
    throw await apiError(response);
  }
  logApiSuccess(method, path, response.status);
  return response;
}

/** Only endpoints with a documented 404-as-empty contract may use this helper. */
export async function fetchApiOrNotFound<T>(path: string, notFound: T): Promise<T> {
  const response = await checkedRequest("GET", path, {
    method: "GET", headers: { Accept: "application/json" }, cache: "no-store",
  }, true);
  return response.status === 404 ? notFound : parseApiResponse<T>(response);
}

/** Binary responses bypass JSON unwrapping and retain the export error contract. */
export async function postBlobApi(path: string, payload: unknown): Promise<Blob> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Export failed with status ${response.status}`);
  return response.blob();
}

async function jsonMutation<T>(method: string, path: string, payload: unknown): Promise<T> {
  return parseApiResponse<T>(await checkedRequest(method, path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }));
}

export async function postApi<T>(path: string, payload: unknown): Promise<T> {
  return jsonMutation<T>("POST", path, payload);
}

export async function patchApi<T>(path: string, payload: unknown): Promise<T> {
  return jsonMutation<T>("PATCH", path, payload);
}

export async function putApi<T>(path: string, payload: unknown): Promise<T> {
  return jsonMutation<T>("PUT", path, payload);
}

export async function postFormApi<T>(path: string, formData: FormData): Promise<T> {
  return parseApiResponse<T>(await checkedRequest("POST", path, { method: "POST", body: formData }));
}

export const postApiFormData = postFormApi;

export async function deleteApi(path: string): Promise<void> {
  await checkedRequest("DELETE", path, { method: "DELETE" });
}

const api = {
  async get<T = unknown>(path: string): Promise<ApiResponse<T>> {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      cache: "no-store",
    });
    if (!response.ok) {
      throw await apiError(response);
    }
    return response.json() as Promise<ApiResponse<T>>;
  },
  async post<T = unknown>(path: string, payload?: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload ? JSON.stringify(payload) : undefined,
    });
    if (!response.ok) {
      throw await apiError(response);
    }
    return response.json() as Promise<ApiResponse<T>>;
  },
};

export default api;
