import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";


test("evidence drawer uses typed alert and event contracts with explicit data states", () => {
  const drawer = readFileSync(
    path.resolve("components/intelligence/EvidenceTrailDrawer.tsx"),
    "utf8",
  );

  assert.match(drawer, /fetchApiResponse<EvidenceTrail>/);
  assert.match(drawer, /`\/alerts\/\$\{alertId\}\/evidence-trail`/);
  assert.match(drawer, /`\/events\/\$\{eventId\}\/evidence-trail`/);
  assert.match(drawer, /trail\.evidence_status !== "complete"/);
  assert.match(drawer, /trail\.claim_type/);
  assert.match(drawer, /trail\.locator\.precision/);
  assert.match(drawer, /DataFreshnessIndicator/);
  assert.match(drawer, /aria-modal="true"/);
  assert.doesNotMatch(drawer, /useState<any>/);
  assert.doesNotMatch(drawer, /dangerouslySetInnerHTML/);
});


test("alert surfaces use the owned alert evidence endpoint and have a real detail route", () => {
  const panel = readFileSync(path.resolve("components/alerts-panel.tsx"), "utf8");
  const alertsPage = readFileSync(path.resolve("app/alerts/page.tsx"), "utf8");
  const detailPage = readFileSync(path.resolve("app/alerts/[id]/page.tsx"), "utf8");

  assert.match(panel, /alertId=\{selectedAlertId\}/);
  assert.match(panel, /href=\{`\/alerts\/\$\{alert\.id\}`\}/);
  assert.match(alertsPage, /EvidenceTrailDrawerWrapper alertId=\{alert\.id\}/);
  assert.match(detailPage, /serverFetchApiResponse<EvidenceTrail>/);
  assert.match(detailPage, /`\/alerts\/\$\{alertId\}\/evidence-trail`/);
  assert.match(detailPage, /evidence\.evidence_status/);
});
