import type { Metadata } from "next";
import type { ReactNode } from "react";
import { WORKSPACE_THEME_KEY } from "@/lib/workspace-chrome";
import "./globals.css";

export const metadata: Metadata = {
  title: "Marketagent",
  description: "Local source-backed market intelligence dashboard"
};

import { AppShell } from "@/components/app-shell";
import { AuthProvider } from "@/components/auth-provider";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `try { document.documentElement.dataset.theme = localStorage.getItem(${JSON.stringify(WORKSPACE_THEME_KEY)}) === "dark" ? "dark" : "light"; } catch {}` }} />
      </head>
      <body>
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
