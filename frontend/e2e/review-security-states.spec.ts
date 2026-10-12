import { expect, test } from "@playwright/test";
import { backendData, signIn } from "./helpers";

test("exact citation checks leave incorrect Mock Data interpretation pending for human review", async ({page}) => {
  await signIn(page);
  const documents = await backendData<Array<{id:number; title:string}>>(page, "/raw-documents/summaries");
  const sourceDocument = documents.find(row => row.title === "Mock Data citation does not prove interpretation")!;
  expect(sourceDocument).toBeTruthy();
  let providerRequests = 0;
  page.on("request", request => {
    if (/generate|analyze/.test(request.url()) && request.method() === "POST") providerRequests++;
  });
  await page.setViewportSize({width:390, height:844});
  await page.goto(`/documents/${sourceDocument.id}/ai`);
  const review = page.getByRole("region", {name:"AI evidence and review"});
  await expect(review.getByText(/Interpretation quality is not evaluated/)).toBeVisible();
  await expect(review.getByRole("button", {name:"Approve", exact:true})).toBeDisabled();
  await review.getByLabel(/^Exact supporting passage/).fill("Revenue increased 12% in FY2025.");
  await review.getByRole("button", {name:"Validate all cited sources"}).click();
  await expect(review.getByText("Exact citation verified.", {exact:true})).toBeVisible();
  await expect(review.getByText("Status: pending", {exact:true})).toBeVisible();
  const outputs = await backendData<Array<{evaluation_json:{interpretation_quality:string}; human_review_status:string}>>(
    page, `/raw-documents/${sourceDocument.id}/ai-outputs`);
  expect(outputs[0].evaluation_json.interpretation_quality).toBe("not_evaluated");
  expect(outputs[0].human_review_status).toBe("pending");
  await review.getByLabel("Review notes", {exact:true}).fill("Mock Data: Incorrect number and fiscal period despite an exact supporting quote.");
  await review.getByRole("button", {name:"Request revision", exact:true}).click();
  await expect(review.getByText("Status: needs revision", {exact:true})).toBeVisible();
  await expect(page.getByText(/^Review Status:\s+needs revision$/i)).toBeVisible();
  expect(providerRequests).toBe(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.screenshot({path:test.info().outputPath("ai-review-boundary-mobile.png"),fullPage:true});
});

test("an invalidated local session cannot reopen private pages or access the backend proxy", async ({page}) => {
  await signIn(page);
  const cookies = await page.context().cookies();
  const session = cookies.find(cookie => cookie.name.includes("session-token"))!;
  expect(session).toBeTruthy();
  await page.context().clearCookies();
  await page.context().addCookies([{...session, value:"invalid-session-signature"}]);
  const response = await page.request.get("/api/backend/portfolios");
  expect(response.status()).toBe(401);
  expect((await response.json()).data).toBeNull();
  await page.goto("/portfolio");
  await expect(page).toHaveURL(/\/auth\/signin/);
  await expect(page.getByRole("button", {name:"Sign in", exact:true})).toBeEnabled();
  await expect(page.getByText("Mock Data Multi-Currency Portfolio", {exact:true})).toHaveCount(0);
});
