"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { WORKSPACE_THEME_KEY, workspaceTheme, type WorkspaceTheme } from "@/lib/workspace-chrome";

export function ThemeSwitch() {
  const [theme, setTheme] = useState<WorkspaceTheme>("light");
  useEffect(() => {
    const apply = (value: WorkspaceTheme) => {
      document.documentElement.dataset.theme = value;
      setTheme(value);
    };
    try { apply(workspaceTheme(localStorage.getItem(WORKSPACE_THEME_KEY))); } catch { apply("light"); }
    const sync = (event: StorageEvent) => {
      if (event.key === WORKSPACE_THEME_KEY || event.key === null) apply(workspaceTheme(event.newValue));
    };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);

  function choose(value: WorkspaceTheme) {
    setTheme(value);
    document.documentElement.dataset.theme = value;
    try { localStorage.setItem(WORKSPACE_THEME_KEY, value); } catch { /* Theme remains usable for this session. */ }
  }

  return <div className="theme-switch" role="group" aria-label="Color theme">
    <button type="button" aria-label="Use light theme" aria-pressed={theme === "light"} onClick={() => choose("light")}><Sun size={15} aria-hidden="true" /></button>
    <button type="button" aria-label="Use dark theme" aria-pressed={theme === "dark"} onClick={() => choose("dark")}><Moon size={15} aria-hidden="true" /></button>
  </div>;
}
