"use client";

import Link from "next/link";
import { LogIn, LogOut, ShieldCheck } from "lucide-react";
import { signOut, useSession } from "next-auth/react";
import { usePathname } from "next/navigation";
import { workspaceLocation } from "@/lib/workspace-chrome";
import { ResearchCommandPalette } from "./research-command-palette";

export function TopBar() {
  const { data: session, status } = useSession();
  const pathname = usePathname();
  return (
    <header className="topbar">
      <nav className="workspace-breadcrumb" aria-label="Breadcrumb"><Link prefetch={false} href="/">Workspace</Link><span aria-hidden="true">/</span><span aria-current="page">{workspaceLocation(pathname)}</span></nav>
      <div className="topbar-actions">
        <Link prefetch={false} href="/data-health" className="data-freshness">
          <ShieldCheck size={16} aria-hidden="true" />Data health
        </Link>
        <div className="user-controls">
          <ResearchCommandPalette />
          {status === "authenticated" ? (
            <button className="secondary-button" type="button" onClick={() => signOut({ callbackUrl: "/" })} title="Sign out" aria-label="Sign out">
              <LogOut size={16} aria-hidden="true" />
              <span>{session.user?.name || "Sign out"}</span>
            </button>
          ) : status === "unauthenticated" ? (
            <Link prefetch={false} href="/auth/signin" className="secondary-button" title="Sign in">
              <LogIn size={16} />
              <span>Sign in</span>
            </Link>
          ) : <span className="muted" role="status">Loading account…</span>}
        </div>
      </div>
    </header>
  );
}
