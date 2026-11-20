"use client";

import { useRouter } from "next/navigation";
import { Company } from "@/lib/api";
import { IndustryMappingCard } from "@/components/valuation/industry-mapping-card";

export function IndustryMappingSection({ company, benchmarkCountry }: { company: Company; benchmarkCountry: string }) {
  const router = useRouter();

  return (
    <IndustryMappingCard
      company={company}
      benchmarkCountry={benchmarkCountry}
      onConfirmed={() => {
        router.refresh();
      }}
      onAutofillDrafted={async () => {
        router.push(`/companies/${company.id}/valuation/draft`);
      }}
    />
  );
}
