"use client";

import { useRouter } from "next/navigation";
import { Company } from "@/lib/api";
import { IndustryMappingCard } from "@/components/valuation/industry-mapping-card";

export function IndustryMappingSection({ company }: { company: Company }) {
  const router = useRouter();

  return (
    <IndustryMappingCard
      company={company}
      onConfirmed={() => {
        router.refresh();
      }}
      onAutofillDrafted={async () => {
        router.push(`/companies/${company.id}/valuation/draft`);
      }}
    />
  );
}
