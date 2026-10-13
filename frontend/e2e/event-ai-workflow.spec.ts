import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { backendData, signIn } from "./helpers";

async function openEvent(page: Page) {
  await signIn(page);
  const event = await backendData<{id: number; title: string; description: string}>(page, "/events", {
    method: "POST", data: {title: `Mock Data AI event ${Date.now()}`, description: "Mock Data source excerpt for interpretation testing.",
      event_type: "manual", information_speed: "slow"}});
  await page.goto("/events");
  const row = page.getByRole("row").filter({has: page.getByRole("cell", {name: event.title, exact: true})});
  await row.getByText("DCF Impact Prediction", {exact: true}).click();
  return {event, panel: row.getByRole("region", {name: "Event AI interpretation"})};
}

test("event AI needs disclosure and unconfigured provider failure leaves the event unchanged", async ({page}) => {
  const {event, panel} = await openEvent(page);
  const button = panel.getByRole("button", {name: "Analyze DCF impact"});
  await expect(button).toBeDisabled();
  const response = await page.request.post("/api/backend/ai/research/map-event-to-dcf", {
    headers: {origin: new URL(page.url()).origin}, data: {event_id: event.id, event_text: `${event.title}\n${event.description}`}});
  expect(response.status()).toBe(409);
  await panel.getByRole("checkbox").check();
  await button.click();
  await expect(panel.getByRole("alert")).toContainText("AI is not configured");
  await expect(panel.getByLabel("Event interpretation result")).toHaveCount(0);
  expect(await backendData(page, `/events/${event.id}`)).toEqual(event);
  await expect(button).toBeEnabled();
});

for (const width of [1440, 390]) {
  test(`event AI ignores revoked consent and presents only a verified pending interpretation at ${width}px`, async ({page}) => {
    await page.setViewportSize({width, height: 900});
    const {event, panel} = await openEvent(page);
    const literal = "Mock Data <script>window.unsafeEventInterpretation = true</script>";
    const data = {impacted_variables: [{variable_name: "Revenue Growth Rate", impact_direction: "unknown", confidence: "low", reasoning: literal}],
      ai_output_id: 900001, model_name: "Mock Data browser fixture", ai_output: {
        id: 900001, reference_type: "event", reference_id: event.id, execution_status: "success", is_mock: true,
        human_review_status: "pending", is_blocked: true, source_ids_json: [`event:${event.id}`],
        provider_name: "mock", model_name: "Mock Data browser fixture", created_at: "2026-10-13T00:00:00Z",
        prompt_version: "Mock Data event fixture", input_hash: "a".repeat(64), limitations: "Mock Data UI fixture. No provider was called."}};
    let release!: () => void;
    const held = new Promise<void>(resolve => {release = resolve;});
    let began!: () => void;
    const started = new Promise<void>(resolve => {began = resolve;});
    let attempts = 0;
    await page.route("**/api/backend/ai/research/map-event-to-dcf", async route => {
      attempts++;
      expect(route.request().postDataJSON()).toEqual({event_id: event.id,
        event_text: `${event.title}\n${event.description}`, privacy_disclosure_version: "v1"});
      if (attempts === 1) {began(); await held;}
      await route.fulfill({json: {data: attempts === 3 ? {...data, ai_output: {...data.ai_output, reference_id: event.id + 1}} : data,
        errors: [], meta: {is_mock: true}}}).catch(() => {});
    });
    try {
      await panel.getByRole("checkbox").check();
      await panel.getByRole("button", {name: "Analyze DCF impact"}).click();
      await started;
      await expect(panel.getByRole("button", {name: "Interpreting event…"})).toBeDisabled();
      await panel.getByRole("checkbox").uncheck();
      const completed = page.waitForResponse("**/api/backend/ai/research/map-event-to-dcf");
      release(); await completed;
      await expect(panel.getByLabel("Event interpretation result")).toHaveCount(0);
      await expect(panel.getByRole("button", {name: "Analyze DCF impact"})).toBeDisabled();
      await panel.getByRole("checkbox").check();
      await panel.getByRole("button", {name: "Analyze DCF impact"}).click();
      await expect(panel.getByText(literal, {exact: true})).toBeVisible();
      await expect(panel).toContainText("Mock Data · AI Interpretation");
      await expect(panel).toContainText("Human review: pending");
      await expect(panel).toContainText("Evidence checks have not verified these claims");
      await panel.getByText("Source and generation evidence", {exact: true}).click();
      await expect(panel).toContainText("a".repeat(64));
      await expect(panel.getByRole("link", {name: "Review the recorded event and source evidence"})).toHaveAttribute("href", `/events/${event.id}/evidence-resolution`);
      expect(await page.evaluate(() => "unsafeEventInterpretation" in window)).toBe(false);
      expect((await panel.boundingBox())!.width).toBeGreaterThanOrEqual(280);
      expect(await panel.evaluate(element => {
        const panel = element.getBoundingClientRect();
        const parent = element.closest("details")!.getBoundingClientRect();
        return panel.left >= parent.left && panel.right <= parent.right;
      })).toBe(true);
      expect((await new AxeBuilder({page}).include('section[aria-label="Event AI interpretation"]').withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      await panel.screenshot({path: test.info().outputPath(`event-ai-${width}.png`)});
      await panel.getByRole("button", {name: "Analyze DCF impact"}).click();
      await expect(panel.getByRole("alert")).toContainText("could not be verified");
      await expect(panel.getByLabel("Event interpretation result")).toHaveCount(0);
      expect(attempts).toBe(3);
      expect(await backendData(page, `/events/${event.id}`)).toEqual(event);
    } finally {release();}
  });
}
