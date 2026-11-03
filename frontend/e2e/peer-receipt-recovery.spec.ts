import { expect, test } from "@playwright/test";
import { backendData, signIn } from "./helpers";
for (const receiptStatus of ["missing", "stale"] as const) {
  test(`Data Health recovers a ${receiptStatus} peer receipt and persists the exact acknowledgement`, async ({page}) => {
    await signIn(page);
    await page.setViewportSize({width:390, height:844});
    const name = `Mock Data ${receiptStatus} receipt recovery`;
    type PeerSet = {id:number;companyId:number;name:string;version:number;reviewStatus:string;
      reviewReceipt:null|{diagnosticsSha256:string;warningCodes:string[];diagnosticsAsOf:string;matchesCurrentDiagnostics:boolean};
      diagnostics:{acknowledgementSha256:string;warningCodes:string[];asOf:string};
      calculationEligibility:{canCalculate:boolean;blockers:string[]}};
    const sets = await backendData<Array<{id:number;name:string}>>(page, "/api/valuation/relative/peer-sets");
    const fixture = sets.find(set => set.name === name);
    expect(fixture, "Fresh isolated receipt fixture must be seeded; do not silently skip recovery proof").toBeTruthy();
    const before = await backendData<PeerSet>(page, `/api/valuation/relative/peer-sets/${fixture!.id}`);
    expect(before.reviewStatus).toBe("reviewed");
    expect(before.calculationEligibility.canCalculate).toBe(false);
    expect(before.calculationEligibility.blockers).toContain(`receipt_${receiptStatus}`);
    // Scope the bounded health page to include this set even if other workflows created many sets.
    const cursor = before.id - 1;
    const healthPath = `/data-health/peer-review-receipts?limit=50&after_id=${cursor}`;
    type Health = {sets_requiring_attention:Array<{peer_set_id:number;receipt_status:string}>;ready_for_valuation_count:number};
    const healthBefore = await backendData<Health>(page, healthPath);
    expect(healthBefore.sets_requiring_attention).toContainEqual(expect.objectContaining({peer_set_id:before.id,receipt_status:receiptStatus}));
    await page.goto(`/data-health?peer_after=${cursor}`);
    const healthPanel = page.locator("section.panel").filter({has:page.getByRole("heading", {name:"Peer Review Receipts", exact:true})});
    const link = healthPanel.getByRole("link", {name:`${name} (v${before.version})`, exact:true});
    await expect(link).toHaveAttribute("href", `/companies/${before.companyId}/valuation/peers#peer-set-${before.id}`);
    await expect(healthPanel.getByRole("row").filter({has:page.getByRole("link", {name:`${name} (v${before.version})`, exact:true})})).toContainText(receiptStatus);
    await link.click();
    const card = page.locator(`#peer-set-${before.id}`);
    await expect(card).toBeVisible();
    await expect(card).toContainText(receiptStatus === "missing" ? "Diagnostic receipt: not recorded" : "Diagnostic receipt: stale");
    const acknowledge = card.getByRole("button", {name:"Re-acknowledge current diagnostics", exact:true});
    if (before.diagnostics.warningCodes.length) {
      await expect(acknowledge).toBeDisabled();
      await card.getByRole("checkbox", {name:"I reviewed the current diagnostic warning categories.", exact:true}).check();
    }
    const reviewedResponse = page.waitForResponse(response => response.request().method() === "POST"
      && new URL(response.url()).pathname === `/api/backend/api/valuation/relative/peer-sets/${before.id}/review`);
    await acknowledge.click();
    const response = await reviewedResponse;
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.errors).toEqual([]);
    expect(body.data.version).toBe(before.version + 1);
    await expect(card).toContainText("Diagnostic receipt: current as of");
    const after = await backendData<PeerSet>(page, `/api/valuation/relative/peer-sets/${before.id}`);
    expect(after.version).toBe(before.version + 1);
    expect(after.reviewReceipt).toEqual({diagnosticsSha256:after.diagnostics.acknowledgementSha256,
      warningCodes:after.diagnostics.warningCodes,diagnosticsAsOf:after.diagnostics.asOf,matchesCurrentDiagnostics:true});
    expect(after.calculationEligibility.canCalculate).toBe(true);
    const history = await backendData<Array<{version:number;action:string;reviewReceipt:PeerSet["reviewReceipt"]}>>(page,
      `/api/valuation/relative/peer-sets/${before.id}/revisions`);
    expect(history[0]).toMatchObject({version:after.version,action:"review",reviewReceipt:after.reviewReceipt});
    await page.goto(`/data-health?peer_after=${cursor}`);
    await expect(healthPanel.getByRole("link", {name:new RegExp(name)})).toHaveCount(0);
    const healthAfter = await backendData<Health>(page, healthPath);
    expect(healthAfter.sets_requiring_attention.some(set => set.peer_set_id === before.id)).toBe(false);
    expect(healthAfter.ready_for_valuation_count).toBeGreaterThanOrEqual(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await page.screenshot({path:test.info().outputPath(`peer-${receiptStatus}-recovered-mobile.png`),fullPage:true});
  });
}
