import { expect, test } from "@playwright/test";
import { backendData, signIn } from "./helpers";

test("a failed source save keeps entries and can be explicitly retried", async ({page}) => {
  await signIn(page);
  await page.goto("/sources");
  const label = `Mock Data interrupted source ${Date.now()}`;
  await page.locator("main #name").fill(label);
  await page.locator("main #source_type").fill("manual");
  let fail = true;
  let release!: () => void;
  const delayed = new Promise<void>(resolve => {release = resolve;});
  await page.route("**/sources", async route => {
    if (route.request().method() !== "POST") return route.continue();
    if (fail) return route.abort("failed");
    await delayed;
    return route.continue();
  });
  await page.getByRole("button", {name: "Add source", exact: true}).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("entries are retained");
  await expect(page.locator("main #name")).toHaveValue(label);
  fail = false;
  await page.getByRole("button", {name: "Add source", exact: true}).click();
  await expect(page.locator("main #name")).toBeDisabled();
  await expect(page.getByRole("button", {name: "Add source", exact: true})).toBeDisabled();
  await expect(page.getByRole("main").getByText("Waiting for confirmation…", {exact: true})).toBeVisible();
  await expect(page.getByText("Completed.", {exact: true})).toHaveCount(0);
  release();
  await expect(page.getByRole("row").filter({hasText: label})).toBeVisible();
  expect((await backendData<Array<{name: string}>>(page, "/sources")).filter(source => source.name === label)).toHaveLength(1);
});

test("manual source controls create, edit, preserve zero reliability and delete an unused fixture", async ({page}) => {
  await signIn(page);
  const label = `Mock Data manual source ${Date.now()}`;
  await page.goto("/sources");
  await page.locator("main #name").fill(label);
  await page.locator("main #source_type").fill("manual");
  await page.locator("main #reliability_score").fill("0");
  await page.locator("main #base_url").fill("https://example.invalid/mock-source");
  await page.locator("main #active").uncheck();
  await page.getByRole("button", {name: "Add source", exact: true}).click();
  const row = page.getByRole("row").filter({hasText: label});
  await expect(row).toBeVisible();
  await row.getByText("Edit", {exact: true}).click();
  await row.getByLabel("Name", {exact: true}).fill(label + " revised");
  await row.getByRole("button", {name: "Save", exact: true}).click();
  await expect(row.locator("td").first()).toHaveText(label + " revised");
  const sources = await backendData<Array<{id: number; name: string; active: boolean; reliability_score: number}>>(page, "/sources");
  const source = sources.find(item => item.name === label + " revised")!;
  expect(source).toBeTruthy();
  expect(source.reliability_score).toBe(0);
  expect(source.active).toBe(false);
  await row.getByRole("button", {name: "Delete", exact: true}).click();
  await expect(row).toHaveCount(0);
  expect((await backendData<Array<{id: number}>>(page, "/sources")).some(item => item.id === source.id)).toBe(false);
});

test("manual narrative and pasted social text remain literal and have working edit and removal paths", async ({page}) => {
  await signIn(page);
  const label = `Mock Data narrative ${Date.now()}`;
  await page.goto("/narratives");
  await page.locator("summary").filter({hasText: "Track a New Narrative"}).click();
  await page.getByLabel("Narrative Name", {exact: true}).fill(label);
  await page.getByLabel("Description", {exact: true}).fill("Mock Data manual interpretation, not an AI conclusion");
  await page.getByRole("button", {name: "Create Narrative", exact: true}).click();
  const heading = page.getByRole("heading", {name: label, exact: true});
  await expect(heading).toBeVisible();
  const panel = heading.locator("xpath=ancestor::section[1]");
  const literal = "Mock Data <script>window.insecureClaim = true</script>";
  await panel.getByLabel(`Claim text for ${label}`).fill(literal);
  await panel.getByRole("button", {name: "+ Claim", exact: true}).click();
  await expect(panel.getByText(literal, {exact: true})).toBeVisible();
  expect(await page.evaluate(() => "insecureClaim" in window)).toBe(false);
  await page.goto("/social");
  const social = `Mock Data pasted source ${Date.now()}`;
  await page.getByLabel("Platform", {exact: true}).fill("Manual public excerpt");
  await page.getByLabel("Source URL", {exact: true}).fill("https://example.invalid/mock-post");
  await page.getByLabel("Raw Text", {exact: true}).fill(social);
  await page.getByRole("button", {name: "Import Post", exact: true}).click();
  const row = page.getByRole("row").filter({hasText: social});
  await expect(row).toBeVisible();
  await row.getByText("Edit", {exact: true}).click();
  await row.getByLabel("Raw Text", {exact: true}).fill(social + " corrected");
  await row.getByRole("button", {name: "Save", exact: true}).click();
  await expect(row.getByText(social + " corrected", {exact: true})).toBeVisible();
  await row.getByRole("button", {name: "Delete", exact: true}).click();
  await expect(row).toHaveCount(0);
  await page.goto("/narratives");
  await panel.getByRole("button", {name: "Delete", exact: true}).click();
  await expect(heading).toHaveCount(0);
});

test("research transport and permission failures retain the question without claiming a save", async ({page}) => {
  await signIn(page);
  const session = await backendData<{id: number}>(page, "/research/sessions", {method: "POST", data: {title: "Mock Data message recovery"}});
  await page.goto(`/research/sessions/${session.id}`);
  const input = page.getByRole("textbox", {name: "Research question"});
  const content = "Mock Data message requiring save confirmation";
  await input.fill(content);
  await page.getByRole("checkbox").check();
  let fail = true;
  await page.route(`**/api/backend/research/sessions/${session.id}/messages`, route => fail ? route.abort("failed") : route.fulfill({
    status: 409,
    json: {errors: [{code: "AI_CONSENT_REQUIRED", message: "Mock Data: No current permission allows this AI action. Review AI permissions in Settings before trying again."}]},
  }));
  await page.getByRole("button", {name: "Send", exact: true}).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("Save could not be confirmed");
  await expect(input).toHaveValue(content);
  await expect(page.getByText(/Your research message was saved/)).toHaveCount(0);
  expect((await backendData<{messages: unknown[]}>(page, `/research/sessions/${session.id}`)).messages).toHaveLength(0);
  fail = false;
  await page.getByRole("button", {name: "Send", exact: true}).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("No current permission allows this AI action");
  await expect(page.locator("main").getByRole("alert")).toContainText("Save could not be confirmed");
  await expect(input).toHaveValue(content);
  await expect(page.getByText(/Your research message was saved/)).toHaveCount(0);
  const stored = await backendData<{messages: Array<{role: string; content: string}>}>(page, `/research/sessions/${session.id}`);
  expect(stored.messages).toHaveLength(0);
});

test("a Mock Data post-save provider failure confirms only the refreshed user message", async ({page}) => {
  // Presentation proof only. The isolated backend regression verifies actual post-grant persistence.
  const sessionId = 984201;
  const content = "Mock Data question saved before provider failure";
  let sent = 0;
  const messages: Array<{id: number; role: string; content: string; created_at: string; ai_output: null}> = [];
  await page.route(`**/api/backend/research/sessions/${sessionId}`, async route => {
    expect(route.request().method()).toBe("GET");
    await route.fulfill({json: {data: {id: sessionId, title: "Mock Data provider failure receipt", messages},
      meta: {status: "success", source: "Mock Data browser fixture", is_mock: true}, errors: []}});
  });
  await page.route(`**/api/backend/research/sessions/${sessionId}/messages`, async route => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().postDataJSON()).toEqual({role: "user", content, privacy_disclosure_version: "v1"});
    sent++;
    messages.push({id: 984202, role: "user", content, created_at: "2026-11-04T12:00:00Z", ai_output: null});
    await route.fulfill({status: 502, json: {errors: [{code: "AI_PROVIDER_FAILED", message: "Mock Data: The AI provider could not complete the request."}]}});
  });
  await signIn(page);
  await page.goto(`/research/sessions/${sessionId}`);
  const input = page.getByRole("textbox", {name: "Research question"});
  await expect(page.getByText("No messages yet. Start the research session by asking a question.")).toBeVisible();
  await input.fill(content);
  await expect(page.getByRole("button", {name: "Send", exact: true})).toBeDisabled();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", {name: "Send", exact: true}).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("The AI provider could not complete the request");
  await expect(page.locator("main").getByRole("alert")).toContainText("Your research message was saved without an assistant response");
  await expect(page.locator("main").getByRole("alert")).not.toContainText("Save could not be confirmed");
  await expect(input).toHaveValue("");
  await expect(page.locator("#message-984202")).toContainText(content);
  await expect(page.locator("main [id^=message-]")).toHaveCount(1);
  await expect(page.locator("main [id^=ai-output-]")).toHaveCount(0);
  await expect(page.getByRole("button", {name: "Send", exact: true})).toBeDisabled();
  expect(sent).toBe(1);
  expect(messages).toHaveLength(1);
  expect(messages[0]).toMatchObject({role: "user", content, ai_output: null});
});
