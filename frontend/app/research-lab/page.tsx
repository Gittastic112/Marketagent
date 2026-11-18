import { PageHeader } from "@/components/page";
import { ResearchWorkbench } from "@/components/research-lab/research-workbench";
import { SourceAdapterPanel } from "@/components/research-lab/source-adapter-panel";
import { MarketAdapterPanel } from "@/components/research-lab/market-adapter-panel";

export default function ResearchLabPage() {
  return <>
    <PageHeader eyebrow="Research tools" title="Research Lab" description="Run explicit allocation scenarios, rebalancing experiments, return reports and reference-based peer discovery." />
    <ResearchWorkbench />
    <div className="research-lab-workbench"><SourceAdapterPanel /><MarketAdapterPanel /></div>
  </>;
}
