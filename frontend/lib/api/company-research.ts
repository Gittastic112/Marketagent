export type CompanyResearchProfile = {
  id: number; ticker: string; name: string; sector: string | null; industry: string | null;
  country: string | null; currency: string | null; primary_exchange: string | null; exchange: string | null;
  business_status: string; excerpt: string | null; document_title: string | null; published_at: string | null;
  source_href: string | null; basis: string; warnings: string[];
};
