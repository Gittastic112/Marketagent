import Link from "next/link";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/companies", label: "Companies" },
  { href: "/narratives", label: "Narratives" },
  { href: "/research", label: "Research" },
  { href: "/valuation", label: "Valuation" },
  { href: "/data", label: "Data / Ingestion" },
  { href: "/settings", label: "Settings" }
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">Market Intelligence</div>
      <nav className="nav" aria-label="Primary navigation">
        {navItems.map((item) => (
          <Link href={item.href} key={item.href}>
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
