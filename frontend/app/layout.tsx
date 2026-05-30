import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Market Intelligence Engine",
  description: "Local source-backed market intelligence dashboard"
};

import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/topbar";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <Sidebar />
          <div className="main-content-wrapper">
            <TopBar />
            <main className="main">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
