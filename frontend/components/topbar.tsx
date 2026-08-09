"use client";

import Link from "next/link";
import { LogIn, LogOut, Search, Settings } from "lucide-react";
import { signOut, useSession } from "next-auth/react";

export function TopBar() {
  const { data: session, status } = useSession();
  return (
    <header className="topbar">
      <p className="topbar-context">Source-backed investment research</p>
      <div className="topbar-actions">
        <Link href="/data-health" className="data-freshness">
          Check data health
        </Link>
        <div className="user-controls">
          <Link href="/search" className="secondary-button" aria-label="Search evidence" title="Search evidence">
            <Search size={16} />
          </Link>
          <Link href="/settings" className="secondary-button" aria-label="Settings" title="Settings">
            <Settings size={16} />
          </Link>
          {status === "authenticated" ? (
            <button className="secondary-button" type="button" onClick={() => signOut({ callbackUrl: "/" })} title="Sign out">
              <LogOut size={16} />
              <span>{session.user?.name || "Sign out"}</span>
            </button>
          ) : (
            <Link href="/auth/signin" className="secondary-button" title="Sign in">
              <LogIn size={16} />
              <span>Sign in</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
