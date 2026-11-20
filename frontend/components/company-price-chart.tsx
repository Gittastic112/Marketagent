"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { addPricePin, type PricePin, type PricePoint, type PriceSeries, type PriceTimeline } from "@/lib/api/price-timeline";
import { formatDataLabel, formatNumber } from "@/lib/formatting";

type ThesisChoice = { id: number; title: string };
const dayMs = 86_400_000;
const dateFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
const tickFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
const longDate = (value: string) => dateFormat.format(new Date(value));
const changeLabel = (value: number) => `${value > 0 ? "+" : ""}${formatNumber(value)}%`;
const priceLabel = (price: number, currency: string) => `${currency} ${formatNumber(price, price < 1 ? 6 : 2)}`;
const seriesLabel = (series: PriceSeries) =>
  [series.claim_type === "Mock Data" && "Mock Data", formatDataLabel(series.provider), series.symbol, series.exchange, series.currency, formatDataLabel(series.adjustment)].filter(Boolean).join(" · ");

function SourceList({ records, query }: { records: PricePoint["sources"]; query: string }) {
  return <ul className="price-detail-list">{records.map(source => <li key={`${source.document_id}-${source.event_id ?? "doc"}`}>
    <Link href={source.event_id ? `/events/${source.event_id}/evidence-resolution?${query}` : `/documents/${source.document_id}/sections?${query}`}>{source.title}</Link>
    <small>{source.sample ? "Mock Data · " : ""}{source.event_id ? `Event on ${source.context_date}` : "Stored source"} · {source.source} · Published {source.published}</small>
    {source.summary && <p>{source.summary}</p>}
    {source.event_id && <Link href={`/documents/${source.document_id}/sections?${query}`}>Open source document</Link>}
  </li>)}</ul>;
}

function PointInspector({ point, series, notes, companyId, pins, precedingSources, initialThesis, onSave }: {
  point: PricePoint; series: PriceSeries; notes: ThesisChoice[] | null; companyId: number;
  pins: PricePin[]; initialThesis?: number; precedingSources: PricePoint["sources"]; onSave: (pin: PricePin) => void;
}) {
  const [thesisId, setThesisId] = useState(notes?.some(n=>n.id===initialThesis) ? String(initialThesis) : notes?.length === 1 ? String(notes[0].id) : "");
  const context = new URLSearchParams({price_series:series.key, price_date:point.date});
  if (thesisId) {
    context.set("note_id",thesisId);
    const pin=pins.find(p=>String(p.thesis_note_id)===thesisId);
    if (pin) context.set("pin",String(pin.id));
  }
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");
  const pending = useRef<{ key: string; id: string } | null>(null);
  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !thesisId || !point.price_id || !point.fingerprint || !body.trim()) return;
    const text = body.trim();
    const key = JSON.stringify([point.fingerprint, thesisId, text]);
    if (pending.current?.key !== key) pending.current = { key, id: crypto.randomUUID() };
    setBusy(true);
    setFeedback("");
    try {
      const pin = await addPricePin(companyId, { thesis_id: Number(thesisId), price_id: point.price_id,
        fingerprint: point.fingerprint, text, request_id: pending.current.id });
      onSave(pin);
      pending.current = null;
      setBody("");
      setFeedback("Saved to your thesis.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "The note could not be saved. Retry with the same text.");
    } finally { setBusy(false); }
  }
  return <>
    <p className="price-inspector-value">{point.price === null ? "Conflicting closes" : priceLabel(point.price, series.currency)}</p>
    {series.claim_type === "Mock Data" && <span className="badge">Mock Data</span>}
    {point.change_pct !== null && point.previous_date
      ? <p>{changeLabel(point.change_pct)} from the stored close on {longDate(point.previous_date)}.</p>
      : <p className="muted">A comparable change is unavailable for this date.</p>}
    <section aria-label="Dated evidence">
      <h3>What happened around this close?</h3>
      {point.sources.length || precedingSources.length ? <>
        <p className="muted">Publication can follow the close. Timing alone cannot establish the cause.</p>
        {point.sources.length > 0 && <SourceList query={context.toString()} records={point.sources} />}
        {precedingSources.length > 0 && point.previous_date && <section aria-label="Preceding close coverage">
          <h4>On the preceding close date · {longDate(point.previous_date)}</h4>
          <SourceList query={context.toString()} records={precedingSources} />
        </section>}
      </> : <p className="muted">No matching dated source is shown. The cause of this move is unverified.</p>}
    </section>
    <section aria-label="Private thesis notes">
      <h3>Your thesis notes</h3>
      {pins.length > 0 && <ul className="price-detail-list">{pins.map(pin => <li key={pin.id}>
        <p className="price-note-text">{pin.text}</p>
        <Link href={`/thesis-notes/${pin.thesis_note_id}#price-pins`}>{notes?.find(note => note.id === pin.thesis_note_id)?.title ?? "Open thesis"}</Link>
      </li>)}</ul>}
      {point.price_id && (notes === null ? <p>Theses could not be loaded. Reload the company to retry.</p>
        : !notes.length ? <Link href="/thesis-notes">Create a thesis for this company to pin a note</Link>
        : <form onSubmit={save} className="price-note-form">
          <label>Attach to thesis<select required disabled={busy} value={thesisId} onChange={e => setThesisId(e.target.value)}>
            <option value="">Choose a thesis</option>{notes.map(note => <option key={note.id} value={note.id}>{note.title}</option>)}
          </select></label>
          <label>Note on this close<textarea disabled={busy} maxLength={2000} required rows={3} value={body} onChange={e => setBody(e.target.value)} /></label>
          <button disabled={busy || !thesisId || !body.trim()} type="submit">{busy ? "Saving…" : "Pin to thesis"}</button>
        </form>)}
      <p role="status">{feedback}</p>
    </section>
  </>;
}

export function CompanyPriceChart({ data, companyId, notes, requestedDate, requestedThesis }: {
  data: PriceTimeline; companyId: number; notes: ThesisChoice[] | null; requestedDate?: string; requestedThesis?: number;
}) {
  const latest = data.points.at(-1);
  const [range, setRange] = useState(0);
  const [date, setDate] = useState(requestedDate ?? latest?.date ?? "");
  const [saved, setSaved] = useState<PricePin[]>([]);
  const dialog = useRef<HTMLDialogElement>(null);
  const series = data.series;
  const seriesChooser = data.choices.length > 1 && <label className="price-series-select">Price series
    <select value={series?.key ?? ""} onChange={event => {
      const url = new URL(window.location.href);
      url.searchParams.set("price_series", event.target.value);
      url.searchParams.delete("price_date");
      url.searchParams.delete("thesis");
      url.searchParams.delete("pin");
      url.hash = "price-history";
      window.location.assign(url);
    }}>{data.choices.map(s => <option value={s.key} key={s.key}>{seriesLabel(s)}</option>)}</select></label>;
  if (!series || !latest) return <>{seriesChooser}<p>No stored daily closes in this view.</p>
    <Link href={requestedDate ? `/companies/${companyId}#price-history` : "/market-prices"}>{requestedDate ? "Show latest history" : "Open price records"}</Link></>;
  const selectedPoints = data.points.filter(p => !range || Date.parse(p.date) >= Date.parse(latest.date) - (range - 1) * dayMs);
  const point = selectedPoints.find(p => p.date === date) ?? selectedPoints[selectedPoints.length - 1];
  const pinsFor = (p: PricePoint) => [...p.pins, ...saved.filter(pin => pin.anchor.price_id === p.price_id && pin.anchor.date === p.date && Number(pin.anchor.price) === p.price && !p.pins.some(old => old.id === pin.id))];
  const moments = selectedPoints.filter(p => p.large_move || p.sources.length || pinsFor(p).length);
  const graph = selectedPoints.flatMap((p, i) => {
    const time = Date.parse(p.date);
    const observation = { time, close: p.price, point: p };
    if (p.gap_before && i) return [{ time: (time + Date.parse(selectedPoints[i - 1].date)) / 2, close: null, point: null }, observation];
    return [observation];
  });
  function inspect(d: string) {
    setDate(d);
    if (!dialog.current?.open) dialog.current?.showModal();
  }
  const marker = ({ cx, cy, payload }: { cx?: number; cy?: number; payload?: { point: PricePoint | null } }) => {
    const p = payload?.point;
    if (!p || cx === undefined || cy === undefined || p.price === null) return <g key={p?.date ?? "gap"} />;
    const source = p.sources.length > 0, pinned = pinsFor(p).length > 0;
    return <g key={p.date} transform={`translate(${cx} ${cy})`} onClick={() => inspect(p.date)}>
      {source && <circle r="6" className="price-source-mark" />}
      {p.large_move && <path d="M0,-5 L5,0 L0,5 L-5,0 Z" className="price-move-mark" />}
      {pinned && <rect x="-3" y="-3" width="6" height="6" className="price-note-mark" />}
      {selectedPoints.length === 1 && !source && !p.large_move && !pinned && <circle r="3.5" fill="var(--color-accent)" />}
    </g>;
  };
  return <>
    <div className="price-chart-toolbar">
      <div><strong className="price-chart-close">{latest.price === null ? "Conflicting closes" : priceLabel(latest.price, series.currency)}</strong>
        <span className="muted">Stored close · {longDate(latest.date)}</span></div>
      <div className="price-range" role="group" aria-label="Chart range">{([[30,"1M"],[90,"3M"],[180,"6M"],[0,"All"]] as const).map(([days,label]) =>
        <button key={label} className="secondary-button" aria-pressed={range === days} type="button" onClick={() => setRange(days)}>{label}</button>)}</div>
    </div>
    <p className="price-chart-basis">{seriesLabel(series)}{data.truncated && " · Most recent 365 stored dates in this view"}</p>
    {seriesChooser}
    <div className="price-chart-plot" role="img" aria-label={`Closing prices in ${series.currency} from ${selectedPoints[0].date} through ${latest.date}. Use Inspect date for individual values and notes.`}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={graph} margin={{ left: 0, right: 15, top: 12, bottom: 4 }}
          onClick={state => { const p = state?.activePayload?.[0]?.payload?.point; if (p) inspect(p.date); }}>
          <CartesianGrid vertical={false} stroke="var(--color-border-default)" strokeDasharray="3 4" />
          <XAxis dataKey="time" type="number" scale="time" domain={["dataMin", "dataMax"]} tickCount={5} minTickGap={38}
            tickFormatter={time => tickFormat.format(new Date(time))} axisLine={false} tickLine={false} />
          <YAxis domain={["auto", "auto"]} width={58} axisLine={false} tickLine={false} tickFormatter={p => formatNumber(p, 2)} />
          <Tooltip labelFormatter={time => dateFormat.format(new Date(Number(time)))} formatter={value => [priceLabel(Number(value), series.currency), "Close"]}
            contentStyle={{ background: "var(--color-surface)", borderColor: "var(--color-border-default)", color: "var(--color-text)" }} />
          <Line type="linear" dataKey="close" stroke="var(--color-accent)" strokeWidth={2} connectNulls={false}
            isAnimationActive={false} dot={marker} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
    <div className="price-chart-legend"><span>◇ Move ≥ {data.move_threshold_pct}%</span><span>○ Dated source</span><span>■ Thesis note</span></div>
    <div className="price-chart-controls">
      <label>Inspect date<select value={point.date} onChange={e => setDate(e.target.value)}>
        {[...selectedPoints].reverse().map(p => <option value={p.date} key={p.date}>{longDate(p.date)}</option>)}</select></label>
      <button className="secondary-button" type="button" onClick={() => inspect(point.date)}>Open point details</button>
      {moments.length > 0 && <label>Key moments<select value="" onChange={e => { if (e.target.value) inspect(e.target.value); }}>
        <option value="">Choose a marked date ({moments.length})</option>
        {[...moments].reverse().map(p => <option key={p.date} value={p.date}>{p.date} · {[
          p.large_move && p.change_pct !== null ? changeLabel(p.change_pct) : "", p.sources.length ? "source" : "", pinsFor(p).length ? "your note" : "",
        ].filter(Boolean).join(" · ")}</option>)}</select></label>}
    </div>
    {series.adjustment === "unadjusted" && <p className="muted price-chart-footnote">Unadjusted closes can move with splits and distributions. Markers compare consecutive stored closes up to seven calendar days apart.</p>}
    {data.context_limited && <p>Only the most recent matching source records were inspected for this window.</p>}
    {requestedDate && <Link href={`/companies/${companyId}#price-history`}>Show latest history</Link>}
    <dialog className="price-point-dialog" ref={dialog} aria-labelledby="price-point-title">
      <div className="price-dialog-heading"><h2 id="price-point-title">{longDate(point.date)}</h2>
        <button className="secondary-button" type="button" onClick={() => dialog.current?.close()}>Close</button></div>
      <PointInspector key={point.date} point={point} series={series} notes={notes} companyId={companyId} initialThesis={requestedThesis}
        precedingSources={data.points.find(p => p.date === point.previous_date)?.sources.filter(s => s.context_date === point.previous_date) ?? []}
        pins={pinsFor(point)} onSave={pin => setSaved(old => old.some(p => p.id === pin.id) ? old : [...old, pin])} />
    </dialog>
  </>;
}
