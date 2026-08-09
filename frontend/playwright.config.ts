import { existsSync } from "node:fs";
import path from "node:path";

import { defineConfig } from "@playwright/test";

const rootEnv = path.resolve(process.cwd(), "..", ".env");
if (existsSync(rootEnv)) {
  process.loadEnvFile(rootEnv);
}

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 120_000,
  expect: {
    timeout: 15_000,
  },
  outputDir: "../output/playwright/test-results",
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:3000",
    channel: process.env.E2E_BROWSER_CHANNEL || "chrome",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "off",
  },
});
