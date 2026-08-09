"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/topbar";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  if (pathname.startsWith("/auth/")) {
    return <main className="auth-shell">{children}</main>;
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content-wrapper">
        <TopBar />
        <main className="main">{children}</main>
      </div>
    </div>
  );
}
