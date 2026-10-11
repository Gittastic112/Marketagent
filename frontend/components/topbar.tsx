"use client";

import Link from "next/link";
import { LogIn, LogOut, Search, ShieldCheck } from "lucide-react";
import { signOut, useSession } from "next-auth/react";

export function TopBar() {
  const { data: session, status } = useSession();
  return (
    <header className="topbar">
      <p className="topbar-context">Personal research <span>Evidence before conviction</span></p>
      <div className="topbar-actions">
        <Link prefetch={false} href="/data-health" className="data-freshness">
          <ShieldCheck size={16} aria-hidden="true" />Data health
        </Link>
        <div className="user-controls">
          <Link prefetch={false} href="/search" className="secondary-button topbar-search-link" aria-label="Search evidence" title="Search evidence">
            <Search size={16} aria-hidden="true" /><span>Search evidence</span>
          </Link>
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
