import { expect, test } from "@playwright/test";

import { backendData, createCompany, signIn } from "./helpers";

test("Mock Data peer review preserves sources and revisions through edits and restore", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {
    ticker: `R${unique}`,
    local_symbol: `R${unique}`,
    name: "Mock Data peer workflow fixture",
  });
  await page.goto(`/companies/${company.id}/valuation/peers`);
  const manager = page.locator("details:visible").filter({ has: page.locator(":scope > summary", { hasText: "Manage reviewed peer sets" }) });
  await manager.getByLabel("Peer-set name").fill("Mock Data lifecycle set");
  await manager.getByLabel("Selection notes").fill("Synthetic browser fixtures in a disposable database. Not genuine company evidence.");
  for (let index = 1; index <= 3; index += 1) {
    const peer = manager.getByRole("group", { name: `Peer ${index}`, exact: true });
    await peer.getByLabel("Identifier", { exact: true }).fill(`FIXTURE${index}`);
    await peer.getByLabel("Source name", { exact: true }).fill("Synthetic annual-filing test fixture");
    await peer.getByLabel("Source URL", { exact: true }).fill(`https://example.com/fixture/${index}`);
    await peer.getByLabel("Source as of", { exact: true }).fill("2026-07-31");
    await peer.getByLabel("Currency", { exact: true }).fill("USD");
    await peer.getByLabel("P/E", { exact: true }).fill(String(10 + index));
  }
  await manager.getByRole("button", { name: "Save draft peer set", exact: true }).click();
  await expect(manager.getByText("Draft peer set saved.", { exact: false })).toBeVisible();
  const sets = await backendData<Array<{ id: number }>>(page, `/api/valuation/relative/peer-sets?company_id=${company.id}&include_archived=true`);
  expect(sets).toHaveLength(1);
  const card = manager.locator(`#peer-set-${sets[0].id}`);
  await expect(card).toContainText("v1 · 3 included peers");
  await expect(card.getByRole("button", { name: "Review and approve" })).toBeDisabled();
  await card.getByRole("checkbox", { name: "I reviewed the current diagnostic warning categories." }).check();
  await card.getByRole("button", { name: "Review and approve" }).click();
  await expect(card).toContainText("v2 · 3 included peers · median · reviewed");
  await expect(card).toContainText("Diagnostic receipt: current as of");

  await card.getByRole("button", { name: "Edit", exact: true }).click();
  await expect(manager.getByLabel("Peer-set name")).toHaveValue("Mock Data lifecycle set");
  await manager.getByRole("group", { name: "Peer 1", exact: true }).getByLabel("P/E", { exact: true }).fill("15");
  await manager.getByRole("button", { name: "Save changes as new version" }).click();
  await expect(card).toContainText("v3 · 3 included peers · median · draft");
  await card.getByRole("button", { name: "Show history" }).click();
  await expect(card.locator("ol")).toContainText("v2");
  await expect(card.locator("ol")).toContainText("reviewed");
  await card.getByRole("button", { name: "Archive", exact: true }).click();
  await expect(card).toContainText("archived");
  await card.getByRole("button", { name: "Restore as draft" }).click();
  await expect(card).toContainText("v5 · 3 included peers · median · draft · active");
  await page.reload();
  await card.getByRole("button", { name: "Edit", exact: true }).click();
  const firstPeer = manager.getByRole("group", { name: "Peer 1", exact: true });
  await expect(firstPeer.getByLabel("P/E", { exact: true })).toHaveValue("15");
  await expect(firstPeer.getByLabel("Source URL", { exact: true })).toHaveValue("https://example.com/fixture/1");
  await expect(firstPeer.getByLabel("Source as of", { exact: true })).toHaveValue("2026-07-31");
});
