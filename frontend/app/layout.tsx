import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { BrowserDebugLogger } from "@/components/browser-debug-logger";
import "./globals.css";

export const metadata: Metadata = {
  title: "Market Intelligence Engine",
  description: "Local source-backed market intelligence dashboard"
};

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/companies", label: "Companies" },
  { href: "/sources", label: "Sources" },
  { href: "/documents", label: "Documents" },
  { href: "/events", label: "Events" },
  { href: "/alerts", label: "Alerts" },
  { href: "/thesis-notes", label: "Thesis Notes" },
  { href: "/daily-brief", label: "Daily Brief" }
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <BrowserDebugLogger />
        <div className="app-shell">
          <aside className="sidebar">
            <div className="brand">Market Intelligence Engine</div>
            <nav className="nav" aria-label="Primary navigation">
              {navItems.map((item) => (
                <Link href={item.href} key={item.href}>
                  {item.label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
