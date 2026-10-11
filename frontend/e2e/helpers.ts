import { expect, type Page } from "@playwright/test";

type BackendOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  data?: unknown;
};

export async function signIn(page: Page): Promise<void> {
  const username = process.env.LOCAL_AUTH_USERNAME;
  const password = process.env.LOCAL_AUTH_PASSWORD;
  if (!username || !password || !process.env.NEXTAUTH_SECRET) {
    throw new Error(
      "LOCAL_AUTH_USERNAME, LOCAL_AUTH_PASSWORD, and NEXTAUTH_SECRET are required for browser workflows.",
    );
  }

  await page.goto("/auth/signin");
  await expect(page.getByRole("button", { name: "Sign in" })).toBeEnabled();
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL("/");
}

export async function backendData<T>(
  page: Page,
  path: string,
  options: BackendOptions = {},
): Promise<T> {
  const method = options.method || "GET";
  const response = await page.request.fetch(`/api/backend${path}`, {
    method,
    data: options.data,
    // APIRequestContext does not add the browser's Origin header automatically.
    // Fixture mutations must obey the same origin boundary as real UI actions.
    headers: {
      accept: "application/json",
      ...(method === "GET" ? {} : { origin: new URL(page.url()).origin }),
    },
  });
  const body = await response.json().catch(() => null);
  expect(
    response.ok(),
    `Backend ${options.method || "GET"} ${path} failed: ${JSON.stringify(body)}`,
  ).toBeTruthy();
  expect(body?.errors || []).toEqual([]);
  return body.data as T;
}

export async function createCompany(
  page: Page,
  overrides: Record<string, unknown>,
): Promise<{ id: number; ticker: string; name: string }> {
  return backendData(page, "/companies", {
    method: "POST",
    data: {
      ticker: "E2E",
      name: "E2E Workflow Company",
      market: "US",
      primary_exchange: "NASDAQ",
      local_symbol: "E2E",
      country: "United States",
      currency: "USD",
      active: true,
      ...overrides,
    },
  });
}
