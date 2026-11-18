import assert from "node:assert/strict";
import test from "node:test";
import { isWorkspaceSearchShortcut, workspaceLocation, workspaceTheme } from "./workspace-chrome.ts";

test("breadcrumbs use route boundaries and never expose private IDs or query strings", () => {
  assert.equal(workspaceLocation("/companies/16/valuation/42?version=19"), "Company valuation");
  assert.equal(workspaceLocation("/companies/16/evidence"), "Company evidence");
  assert.equal(workspaceLocation("/companies/16"), "Company overview");
  assert.equal(workspaceLocation("/research/sessions/17"), "Research sessions");
  assert.equal(workspaceLocation("/research-lab#market-data"), "Research Lab");
  assert.equal(workspaceLocation("/research-labs"), "Research workspace");
  assert.equal(workspaceLocation("/portfolio/regime"), "Market regime");
  assert.equal(workspaceLocation("/data-health"), "Data health");
  assert.equal(workspaceLocation("/data-healthcheck"), "Research workspace");
  assert.equal(workspaceLocation("/"), "Today");
});

test("workspace search preserves input editing, other modifiers and handled keyboard events", () => {
  const key = { key: "k", metaKey: true, ctrlKey: false, altKey: false, shiftKey: false, defaultPrevented: false };
  assert.equal(isWorkspaceSearchShortcut(key, false), true);
  assert.equal(isWorkspaceSearchShortcut({ ...key, metaKey: false, ctrlKey: true }, false), true);
  assert.equal(isWorkspaceSearchShortcut(key, true), false);
  assert.equal(isWorkspaceSearchShortcut({ ...key, metaKey: false }, false), false);
  assert.equal(isWorkspaceSearchShortcut({ ...key, altKey: true }, false), false);
  assert.equal(isWorkspaceSearchShortcut({ ...key, shiftKey: true }, false), false);
  assert.equal(isWorkspaceSearchShortcut({ ...key, defaultPrevented: true }, false), false);
});

test("invalid or absent theme preferences resolve to the default light theme", () => {
  assert.equal(workspaceTheme(null), "light");
  assert.equal(workspaceTheme("unexpected"), "light");
  assert.equal(workspaceTheme("light"), "light");
  assert.equal(workspaceTheme("dark"), "dark");
});
