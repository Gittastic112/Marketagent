import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = (path: string) => readFileSync(path, "utf8");

test("portfolio route loads only the selected server-owned view and preserves 404 versus transport errors", () => {
  const route = source("app/portfolio/[id]/page.tsx");
  assert.match(route, /<Suspense/);
  for (const tab of ["overview", "performance", "activity", "setup"]) assert.ok(route.includes(`tab === "${tab}"`));
  assert.match(route, /error.status === 404/);
  assert.match(route, /throw error/);
  const overview = source("components/portfolio/overview.tsx");
  assert.match(overview, /is_stale_price/);
  assert.match(overview, /market_price_as_of/);
  assert.doesNotMatch(overview, /real-input-readiness|risk-return-comparison|portfolio-snapshots|as_of_date !==/);
});

test("valuation refresh resets inputs without remounting the success notice", () => {
  const page = source("app/companies/[id]/valuation/[model_id]/page.tsx");
  assert.match(page, /key=\{`\$\{companyId\}:\$\{modelId\}`\}/);
  assert.match(source("components/advanced-workspace.tsx"), /<form key=\{latestAssumptionSet\?\.id/);
  assert.match(page, /assumptionsResult.status === "fulfilled" && assumptionsRes\?\.data/);
});

test("mobile navigation contains focus and makes the background inert", () => {
  const nav = source("components/sidebar.tsx");
  for (const guard of ["content.inert = true", 'event.key !== "Tab"', 'event.key === "Escape"', "previousOverflow", "previousInert", "openButtonRef.current?.focus()", 'aria-modal={open ? true : undefined}']) assert.ok(nav.includes(guard), guard);
  assert.match(source("components/app-shell.tsx"), /Skip to content/);
  assert.match(nav, /checkVisibility\(\{ visibilityProperty: true \}\)/);
  assert.match(nav, /!panel\?\.contains\(document.activeElement\)/);
  assert.match(nav, /cancelAnimationFrame\(focusFrame\)/);
});

test("tables preserve whole words inside bounded scrolling panels", () => {
  const styles = source("app/globals.css");
  assert.match(styles, /th,\s*td\s*\{[^}]*overflow-wrap: normal/);
  assert.match(styles, /th\s*\{[^}]*white-space: nowrap/);
  assert.match(styles, /\.sidebar a, \.sidebar button \{ transition-property: color, background-color, border-color/);
  assert.match(source("app/companies/[id]/page.tsx"), /name="tag_id" aria-label="Exposure tag"/);
});
