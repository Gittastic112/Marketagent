import Link from "next/link";
import { PageHeader, Panel } from "@/components/page";

export default function AdvancedPage() {
  return <><PageHeader eyebrow="Specialist tools" title="Advanced research" description="Use these tools when their inputs and limitations fit the question." />
    <Panel title="Analysis"><ul>
      <li><Link href="/valuation/quick">Quick valuation</Link>: an explicit-input estimate; not a replacement for reviewed saved models.</li>
      <li><Link href="/macro">Macro scenarios</Link>: inspect assumptions and source coverage before translating a scenario.</li>
      <li><Link href="/portfolio/regime">Market regime</Link>: market structure and evidence, not a trading signal.</li>
      <li><Link href="/evaluations">Extraction evaluations</Link>: compare extraction with reviewed references without approving candidates.</li>
    </ul></Panel>
    <Panel title="Continue with evidence"><p><Link href="/research">Research library</Link> · <Link href="/companies">Company workspaces</Link> · <Link href="/settings">Configuration and service status</Link></p></Panel>
  </>;
}
