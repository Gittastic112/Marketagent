import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { LoadingState, PageHeader } from "@/components/page";
import { PortfolioOverview } from "@/components/portfolio/overview";
import { PortfolioPerformanceView } from "@/components/portfolio/performance-view";
import { PortfolioActivity } from "@/components/portfolio/activity";
import { PortfolioSetup } from "@/components/portfolio/setup";
import { ApiError } from "@/lib/api/contract";
import type { Portfolio } from "@/lib/api/portfolio";
import { serverFetchApi } from "@/lib/server-api";

export default async function PortfolioDetailPage({
  params, searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const portfolioId = Number(id);
  if (!Number.isSafeInteger(portfolioId) || portfolioId <= 0) notFound();

  let portfolio: Portfolio;
  try {
    portfolio = await serverFetchApi<Portfolio>(`/portfolios/${portfolioId}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error; // A failed request is not a missing portfolio.
  }

  const tab = ["performance", "activity", "setup"].includes(String(query.tab))
    ? String(query.tab) : query.start_date || query.end_date ? "performance" : "overview";
  const tabs = [["overview", "Overview"], ["performance", "Performance & risk"], ["activity", "Activity"], ["setup", "Data & setup"]];
  return (
    <>
      <div className="breadcrumb"><Link href="/portfolio">Portfolios</Link><span>/</span><span>{portfolio.name}</span></div>
      <PageHeader eyebrow="Portfolio research" title={portfolio.name} status={portfolio.base_currency}
        description="Positions, performance and the evidence behind the numbers."
        actions={<Link prefetch={false} className="secondary-button" href="/portfolio/manage">Manage holdings</Link>} />
      {portfolio.description && <p className="basis-note">{portfolio.description}</p>}
      <nav className="workspace-tabs" aria-label="Portfolio sections">
        {tabs.map(([key, label]) => <Link key={key} prefetch={false}
          href={`/portfolio/${portfolioId}${key === "overview" ? "" : `?tab=${key}`}`}
          aria-current={tab === key ? "page" : undefined}>{label}</Link>)}
      </nav>
      <Suspense key={`${tab}:${query.start_date || ""}:${query.end_date || ""}`} fallback={<LoadingState message={`Loading ${tabs.find(([key]) => key === tab)?.[1].toLowerCase()}…`} />}>
        {tab === "overview" && <PortfolioOverview portfolio={portfolio} />}
        {tab === "performance" && <PortfolioPerformanceView portfolio={portfolio} query={query} />}
        {tab === "activity" && <PortfolioActivity portfolio={portfolio} />}
        {tab === "setup" && <PortfolioSetup portfolio={portfolio} />}
      </Suspense>
    </>
  );
}
