import os
import glob
import re

def main():
    frontend_dir = os.path.join("frontend", "app")
    inventory = []

    known_metadata = {
        "/macro/market-regime": {"mock": "Yes (Prototype)", "status": "Prototype"},
        "/companies/[ticker]/fundamentals": {"mock": "No", "status": "Partial"},
        "/daily-brief": {"mock": "No", "status": "Partial"},
        "/portfolio/analytics": {"mock": "No", "status": "Built"},
    }

    pages = glob.glob(os.path.join(frontend_dir, "**", "page.tsx"), recursive=True)

    for page in sorted(pages):
        route = "/" + os.path.relpath(page, frontend_dir).replace("/page.tsx", "").replace("page.tsx", "")
        if route == "/":
            route = "/"

        with open(page, "r") as f:
            content = f.read()

        loading = "Yes" if "LoadingState" in content or os.path.exists(os.path.join(os.path.dirname(page), "loading.tsx")) else "No"
        empty = "Yes" if "EmptyState" in content else "No"
        error = "Yes" if "ErrorState" in content or os.path.exists(os.path.join(os.path.dirname(page), "error.tsx")) else "No"
        stale = "Yes" if "StaleData" in content or "DataFreshnessIndicator" in content or "DataStateNotices" in content else "No"
        partial = "Yes" if "PartialData" in content or "DataStateNotices" in content else "No"
        mock = "Yes" if "MockData" in content or "PrototypeBadge" in content else "No"

        meta = known_metadata.get(route, {})
        status = meta.get("status", "Built")
        mock = meta.get("mock", mock)

        inventory.append(f"| `{route}` | {status} | {loading} | {empty} | {error} | {stale} | {partial} | {mock} |")

    inventory_md = """# Route Inventory

**Updated:** 2026-08-09

This table tracks the implementation of standard data states across all frontend routes, as required by Stage 2.

| Route | Status | Loading | Empty | Error | Stale | Partial | Mock |
|---|---|---|---|---|---|---|---|
""" + "\n".join(inventory) + "\n"

    with open("docs/09-route-inventory.md", "w") as f:
        f.write(inventory_md)
    print("Generated docs/09-route-inventory.md")

if __name__ == "__main__":
    main()
