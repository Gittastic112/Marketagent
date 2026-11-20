import Link from "next/link";

export type ChartReturnQuery = {price_series?: string | string[]; price_date?: string | string[]; note_id?: string | string[]; pin?: string | string[]};

export function ChartReturnLinks({companyId,query}:{companyId:number|null|undefined;query:ChartReturnQuery}) {
  const {price_series:series,price_date:day,note_id:note,pin}=query;
  if (!companyId || typeof series!=="string" || !/^[a-f0-9]{64}$/.test(series) || typeof day!=="string" || !/^\d{4}-\d\d-\d\d$/.test(day)) return null;
  const params=new URLSearchParams({price_series:series,price_date:day});
  const selected=typeof note==="string" && /^[1-9]\d*$/.test(note) ? note : null;
  if(selected){params.set("thesis",selected);if(typeof pin==="string" && /^[1-9]\d*$/.test(pin))params.set("pin",pin);}
  return <nav aria-label="Return to chart research" className="button-row">
    <Link href={`/companies/${companyId}?${params}#price-history`}>Return to selected close</Link>
    {selected && <Link href={`/thesis-notes/${selected}#price-pins`}>Open selected thesis</Link>}
  </nav>;
}
