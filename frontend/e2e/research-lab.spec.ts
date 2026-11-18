import { readFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";
import { signIn } from "./helpers";

const dataset = {
  base_currency: "USD",
  periods_per_year: 252,
  return_basis: "price_return",
  source_label: "Mock Data for the signed-in research simulation",
  assets: [{ key: "EXAMPLE", ticker: "EXAMPLE", currency: "USD" }],
  observations: [
    { start_date: "2025-01-02", end_date: "2025-01-03", returns: { EXAMPLE: 0.1 } },
    { start_date: "2025-01-03", end_date: "2025-01-06", returns: { EXAMPLE: -0.1 } },
  ],
};

for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
  for (const theme of ["light", "dark"]) {
    test(`run, reopen and export a simulation at ${viewport.width}px in ${theme}`, async ({ page }, testInfo) => {
      await page.setViewportSize(viewport);
      await signIn(page);
      await page.goto("/research-lab");
      if (viewport.width === 390) await page.getByRole("button", { name: "Open navigation" }).click();
      await page.getByRole("button", { name: `Use ${theme} theme` }).click();
      if (viewport.width === 390) await page.getByRole("button", { name: "Close navigation panel" }).click();
      await page.reload();
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);

      const simulation = page.getByRole("button", { name: "Rebalancing simulation", exact: true });
      await simulation.click();
      await page.getByLabel("Return dataset JSON", { exact: true }).fill(JSON.stringify(dataset));
      await page.getByLabel("Initial weights JSON", { exact: true }).fill('{"EXAMPLE":1}');
      await page.getByLabel("Weight decision date").fill("2025-01-02");
      const created = page.waitForResponse(response =>
        response.url().endsWith("/api/backend/api/research-lab/simulation") && response.request().method() === "POST");
      await page.getByRole("button", { name: "Run rebalancing simulation" }).click();
      const response = await created;
      expect(response.ok()).toBe(true);
      const { data: saved } = await response.json();
      expect(saved.manifest.input_sha256).toMatch(/^[a-f0-9]{64}$/);
      expect(saved.manifest.output_sha256).toMatch(/^[a-f0-9]{64}$/);
      expect(saved.result.metrics.total_return).toBeCloseTo(-0.01, 10);

      const result = page.getByRole("region", { name: "Saved research result" });
      const heading = result.getByRole("heading", { name: `Saved simulation run #${saved.run_id}` });
      await expect(heading).toBeVisible();
      await page.getByRole("button", { name: "Peer discovery", exact: true }).click();
      await expect(result).toHaveCount(0);
      await page.reload();
      await page.locator("summary").filter({ hasText: "Saved research runs" }).click();
      await page.getByRole("button", { name: `Open run ${saved.run_id}`, exact: true }).click();
      await expect(simulation).toHaveAttribute("aria-pressed", "true");
      await expect(heading).toBeVisible();

      const downloading = page.waitForEvent("download");
      await result.getByRole("link", { name: "Download saved inputs and result (JSON)" }).click();
      const download = await downloading;
      expect(download.suggestedFilename()).toBe(`marketagent-research-${saved.run_id}.json`);
      const file = testInfo.outputPath(download.suggestedFilename());
      await download.saveAs(file);
      const exported = JSON.parse(await readFile(file, "utf8"));
      expect(exported.run_id).toBe(saved.run_id);
      expect(exported.input.dataset).toEqual(dataset);
      expect(exported.manifest).toEqual(saved.manifest);
      expect(exported.result).toEqual(saved.result);
    });
  }
}
