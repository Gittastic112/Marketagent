import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Market Intelligence Engine",
  description: "Local source-backed market intelligence dashboard"
};

import { AppShell } from "@/components/app-shell";
import { AuthProvider } from "@/components/auth-provider";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
