"use client";

import {
  Activity,
  Bell,
  BookOpen,
  BriefcaseBusiness,
  Building2,
  ChartNoAxesCombined,
  Database,
  FileSearch,
  FileWarning,
  Gauge,
  LayoutDashboard,
  Menu,
  Newspaper,
  Settings,
  ShieldCheck,
  TrendingUp,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

type NavGroup = {
  label: string;
  items: NavItem[];
};

const navGroups: NavGroup[] = [
  {
    label: "Today",
    items: [
      { href: "/", label: "Dashboard", icon: LayoutDashboard },
      { href: "/daily-brief", label: "Daily Brief", icon: Newspaper },
      { href: "/alerts", label: "Alerts", icon: Bell },
    ],
  },
  {
    label: "Portfolio",
    items: [
      { href: "/portfolio", label: "Portfolio", icon: BriefcaseBusiness },
      { href: "/portfolio/regime", label: "Market Regime", icon: Gauge },
    ],
  },
  {
    label: "Research",
    items: [
      { href: "/companies", label: "Companies", icon: Building2 },
      { href: "/research", label: "Research", icon: BookOpen },
      { href: "/narratives", label: "Narratives", icon: Activity },
      { href: "/events", label: "Events", icon: TrendingUp },
      { href: "/intelligence/review", label: "Contradictions", icon: FileWarning },
      { href: "/macro", label: "Macro", icon: ChartNoAxesCombined },
      { href: "/valuation", label: "Valuation", icon: ChartNoAxesCombined },
    ],
  },
  {
    label: "Data",
    items: [
      { href: "/documents", label: "Documents", icon: FileSearch },
      { href: "/data", label: "Ingestion", icon: Database },
      { href: "/data-health", label: "Data Health", icon: ShieldCheck },
      { href: "/sources", label: "Sources", icon: Database },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/admin/damodaran", label: "Admin", icon: ShieldCheck },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const openButtonRef = useRef<HTMLButtonElement>(null);
  const allItems = useMemo(() => navGroups.flatMap((group) => group.items), []);
  const activeHref = useMemo(() => {
    const matches = allItems.filter((item) =>
      item.href === "/"
        ? pathname === "/"
        : pathname === item.href || pathname.startsWith(`${item.href}/`),
    );
    return matches.sort((a, b) => b.href.length - a.href.length)[0]?.href;
  }, [allItems, pathname]);

  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeNavigation();
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [open]);

  function closeNavigation() {
    setOpen(false);
    window.requestAnimationFrame(() => openButtonRef.current?.focus());
  }

  return (
    <>
      <div className="mobile-nav-bar">
        <span className="mobile-brand">Market Intelligence</span>
        <button
          ref={openButtonRef}
          type="button"
          className="icon-button"
          aria-label="Open navigation"
          aria-expanded={open}
          onClick={() => setOpen(true)}
        >
          <Menu size={20} />
        </button>
      </div>
      {open ? (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={closeNavigation}
        />
      ) : null}
      <aside className={`sidebar${open ? " sidebar-open" : ""}`}>
        <div className="sidebar-heading">
          <Link href="/" className="brand" prefetch={false}>Market Intelligence</Link>
          <button
            type="button"
            className="icon-button sidebar-close"
            aria-label="Close navigation panel"
            onClick={closeNavigation}
          >
            <X size={20} />
          </button>
        </div>
        <nav className="nav" aria-label="Primary navigation">
          {navGroups.map((group) => (
            <div className="nav-group" key={group.label}>
              <p className="nav-group-label">{group.label}</p>
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    href={item.href}
                    key={item.href}
                    prefetch={false}
                    className={activeHref === item.href ? "active" : ""}
                    aria-current={activeHref === item.href ? "page" : undefined}
                  >
                    <Icon size={17} aria-hidden="true" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
}
