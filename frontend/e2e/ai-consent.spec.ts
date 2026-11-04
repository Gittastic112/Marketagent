import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { signIn } from "./helpers";
import type { AIConsentAction, AIConsentDecision, AIConsentDecisionRequest } from "../lib/api/ai-consent";

// All permission writes are intercepted. These tests never grant real-user access.
async function permissionsFixture(page: Page) {
  let action: AIConsentAction = {provider_name: "gemini", action_key: "document_summary", label: "Document summary",
    description: "Mock Data selected document text <script>window.permissionInjection = true</script>",
    external_data_classes: ["raw_document_text"], disclosure_version: "v1", scope_hash: "a".repeat(64),
    state: "not_granted", current_revision: 0, latest_decision: null};
  const decisions: AIConsentDecision[] = [];
  let writes = 0;
  let unavailable = false;
  const envelope = (data: unknown) => ({data, meta: {status: "success", source: "Mock Data browser fixture", is_mock: true}, errors: []});
  await page.route("**/api/backend/ai/consent**", async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() === "POST") {
      writes++;
      const payload = request.postDataJSON() as AIConsentDecisionRequest;
      expect(payload.provider_name).toBe("gemini");
      expect(payload.action_key).toBe("document_summary");
      expect(payload.scope_hash).toBe(action.scope_hash);
      expect(payload.disclosure_version).toBe("v1");
      if (payload.expected_revision !== action.current_revision) {
        await route.fulfill({status: 409, json: {errors: [{message: "Mock Data permission changed in another request. Reload before deciding again."}]}});
        return;
      }
      const row: AIConsentDecision = {id: decisions.length + 1, provider_name: "gemini", action_key: action.action_key,
        state: payload.state, revision: action.current_revision + 1, disclosure_version: "v1", scope_hash: action.scope_hash,
        external_data_classes: [...action.external_data_classes], created_at: "2026-11-04T12:00:00Z"};
      decisions.unshift(row);
      action = {...action, state: row.state, current_revision: row.revision, latest_decision: row};
      await route.fulfill({json: envelope(row)});
    } else if (unavailable) {
      await route.fulfill({status: 503, json: {errors: [{message: "Mock Data permission service unavailable"}]}});
    } else {
      await route.fulfill({json: envelope(path.endsWith("/history") ? {items: decisions, next_cursor: null}
        : {actions: [action], limitations: ["Mock Data transport fixture. No permission is stored and no provider is called."]})});
    }
  });
  return {writeCount: () => writes, decisions,
    makeUnavailable: () => {unavailable = true;},
    changeInOtherTab: () => {action = {...action, state: "revoked", current_revision: action.current_revision + 1};}};
}

for (const width of [1440, 390]) {
  test(`AI settings require confirmation, preserve decision history and revoke at ${width}px`, async ({page}) => {
    await page.setViewportSize({width, height: 900});
    const fixture = await permissionsFixture(page);
    await signIn(page);
    await page.goto("/settings#ai-permissions");
    const settings = page.getByRole("region", {name: "AI permissions", exact: true});
    const card = settings.getByRole("region", {name: "Document summary", exact: true});
    await expect(card.getByText("Not allowed", {exact: true})).toBeVisible();
    expect(fixture.writeCount()).toBe(0);
    await expect(card.getByRole("button", {name: "Allow", exact: true})).toBeDisabled();
    await card.getByRole("button", {name: "Refuse", exact: true}).click();
    await expect(card.getByText("Refused", {exact: true})).toBeVisible();
    expect(fixture.writeCount()).toBe(1);
    await card.getByRole("checkbox").check();
    await card.getByRole("button", {name: "Allow", exact: true}).click();
    await expect(card.getByText("Allowed", {exact: true})).toBeVisible();
    await expect(card.getByRole("checkbox")).not.toBeChecked();
    await card.getByRole("button", {name: "Revoke", exact: true}).click();
    await expect(card.getByText("Revoked", {exact: true})).toBeVisible();
    expect(fixture.decisions.map(row => row.state)).toEqual(["revoked", "granted", "refused"]);
    await settings.getByText("Permission history", {exact: true}).click();
    await expect(settings.getByText(/Decision #1, revision 1/)).toBeVisible();
    await expect(settings.getByText(/Decision #2, revision 2/)).toBeVisible();
    await expect(settings.getByText(/Decision #3, revision 3/)).toBeVisible();
    await settings.getByRole("button", {name: "Reload permissions"}).click();
    await expect(card.getByText("Revoked", {exact: true})).toBeVisible();
    expect(fixture.writeCount()).toBe(3);
    expect(await page.evaluate(() => Boolean((window as Window & {permissionInjection?: boolean}).permissionInjection))).toBe(false);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    const accessibility = await new AxeBuilder({page}).include("#ai-permissions").withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(accessibility.violations).toEqual([]);
    await page.screenshot({path: test.info().outputPath(`ai-permissions-${width}.png`), fullPage: true});
  });
}

test("stale settings cannot overwrite another decision and unavailable permissions are not shown as cached", async ({page}) => {
  const fixture = await permissionsFixture(page);
  await signIn(page);
  await page.goto("/settings#ai-permissions");
  const settings = page.getByRole("region", {name: "AI permissions", exact: true});
  const card = settings.getByRole("region", {name: "Document summary", exact: true});
  await expect(card.getByText("Not allowed", {exact: true})).toBeVisible();
  await card.getByRole("checkbox").check();
  fixture.changeInOtherTab();
  await card.getByRole("button", {name: "Allow", exact: true}).click();
  await expect(settings.getByRole("alert")).toContainText("changed in another request");
  await expect(card.getByText("Revoked", {exact: true})).toBeVisible();
  expect(fixture.decisions).toEqual([]);
  fixture.makeUnavailable();
  await settings.getByRole("button", {name: "Reload permissions"}).click();
  await expect(settings.getByRole("alert")).toContainText("Permissions are unavailable");
  await expect(card).toHaveCount(0);
  expect(fixture.writeCount()).toBe(1);
});
