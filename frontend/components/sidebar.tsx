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
      { href: "/evaluations", label: "Evaluations", icon: ShieldCheck },
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
  const sidebarRef = useRef<HTMLElement>(null);
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
    const panel = sidebarRef.current;
    const content = document.querySelector<HTMLElement>(".main-content-wrapper");
    const previousOverflow = document.body.style.overflow;
    const previousInert = content?.inert ?? false;
    document.body.style.overflow = "hidden";
    if (content) content.inert = true;
    const focusable = () => Array.from(panel?.querySelectorAll<HTMLElement>('a[href], button, summary, [tabindex="0"]') || [])
      .filter(element => element.checkVisibility({ visibilityProperty: true }));
    const focusFrame = window.requestAnimationFrame(() => focusable()[0]?.focus());
    const containFocus = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); closeNavigation(); }
      if (event.key !== "Tab") return;
      const items = focusable();
      const first = items[0];
      const last = items.at(-1);
      if (!panel?.contains(document.activeElement)) {
        event.preventDefault();
        (event.shiftKey ? last : first)?.focus();
        return;
      }
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    const desktop = window.matchMedia("(min-width: 961px)");
    const closeOnDesktop = () => { if (desktop.matches) setOpen(false); };
    desktop.addEventListener("change", closeOnDesktop);
    document.addEventListener("keydown", containFocus);
    return () => {
      window.cancelAnimationFrame(focusFrame);
      document.body.style.overflow = previousOverflow;
      if (content) content.inert = previousInert;
      document.removeEventListener("keydown", containFocus);
      desktop.removeEventListener("change", closeOnDesktop);
    };
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
          aria-controls="primary-sidebar"
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
          tabIndex={-1}
          onClick={closeNavigation}
        />
      ) : null}
      <aside ref={sidebarRef} id="primary-sidebar" role={open ? "dialog" : undefined} aria-modal={open ? true : undefined} aria-label="Navigation" className={`sidebar${open ? " sidebar-open" : ""}`}>
        <div className="sidebar-heading">
          <Link href="/" className="brand" prefetch={false}><span className="brand-mark" aria-hidden="true">MI</span><span>Market<br />Intelligence</span></Link>
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
          {navGroups.map((group) => {
            const links = group.items.map((item) => {
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
              });
            return ["Data", "System"].includes(group.label)
              ? <details className="nav-group nav-disclosure" key={group.label} open={group.items.some(item => item.href === activeHref)}><summary className="nav-group-label">{group.label}</summary>{links}</details>
              : <div className="nav-group" key={group.label}><p className="nav-group-label">{group.label}</p>{links}</div>;
          })}
        </nav>
      </aside>
    </>
  );
}
