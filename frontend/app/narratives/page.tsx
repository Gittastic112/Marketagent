import { PageHeader } from "@/components/page-header";

export default function NarrativesPage() {
  return (
    <div>
      <PageHeader 
        title="Narrative Intelligence" 
        eyebrow="Market Stories" 
        status="Tracking 0 active narratives" 
      />
      
      <div className="empty">
        Narrative intelligence feature is under construction.
      </div>
    </div>
  );
}
