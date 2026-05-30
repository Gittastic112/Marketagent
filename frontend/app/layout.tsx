import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Market Intelligence Engine",
  description: "Local source-backed market intelligence dashboard"
};

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/companies", label: "Companies" },
  { href: "/research", label: "Research" },
  { href: "/valuation", label: "Valuation" },
  { href: "/alerts", label: "Alerts" },
  { href: "/data", label: "Data" },
  { href: "/settings", label: "Settings" }
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
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
