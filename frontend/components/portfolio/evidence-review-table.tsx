"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { EvidencePreviewRow } from "@/lib/api/portfolio-evidence";
import { EMPTY_EVIDENCE_FILTER, EVIDENCE_REVIEW_PAGE_SIZE, filterEvidenceRows, nextEvidenceIssue, type EvidenceReviewFilter } from "@/lib/evidence-import-review";

export function EvidenceReviewTable({ rows }: { rows: EvidencePreviewRow[] }) {
  const id = useId();
  const [filter, setFilter] = useState<EvidenceReviewFilter>(EMPTY_EVIDENCE_FILTER);
  const [page, setPage] = useState(0);
  const [selectedRow, setSelectedRow] = useState<number | null>(null);
  const [jump, setJump] = useState("");
  const [message, setMessage] = useState("");
  const focusRow = useRef<HTMLTableRowElement>(null);
  const filtered = useMemo(() => filterEvidenceRows(rows, filter), [rows, filter]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / EVIDENCE_REVIEW_PAGE_SIZE));
  const currentPage = Math.min(page, pageCount - 1);
  const visible = filtered.slice(currentPage * EVIDENCE_REVIEW_PAGE_SIZE, (currentPage + 1) * EVIDENCE_REVIEW_PAGE_SIZE);
  const fields = useMemo(() => [...new Set(rows.flatMap(row => row.errors.map(error => error.field)))].sort(), [rows]);
  const issues = rows.filter(row => row.action === "error");

  useEffect(() => { if (selectedRow !== null) focusRow.current?.focus(); }, [selectedRow, currentPage, filter]);

  function updateFilter(patch: Partial<EvidenceReviewFilter>) {
    setFilter(previous => ({ ...previous, ...patch })); setPage(0); setSelectedRow(null); setMessage("");
  }
  function navigateIssue(direction: 1 | -1) {
    const row = nextEvidenceIssue(rows, selectedRow, direction);
    if (row === null) return;
    setFilter({ ...EMPTY_EVIDENCE_FILTER, action: "error" });
    setPage(Math.floor(issues.findIndex(item => item.row_index === row) / EVIDENCE_REVIEW_PAGE_SIZE));
    setSelectedRow(row); setMessage(`CSV row ${row}. Showing error rows.`);
  }
  function jumpToRow() {
    const number = Number(jump);
    const index = rows.findIndex(row => row.row_index === number);
    if (!Number.isInteger(number) || index < 0) { setMessage("That CSV row is not in this preview."); return; }
    setFilter(EMPTY_EVIDENCE_FILTER); setPage(Math.floor(index / EVIDENCE_REVIEW_PAGE_SIZE)); setSelectedRow(number);
    setMessage(`CSV row ${number}. Filters cleared.`);
  }

  return <section className="evidence-row-review" aria-label="Evidence row review">
    <div className="form-grid">
      <div className="field"><label htmlFor={`${id}-status`}>Row status</label>
        <select id={`${id}-status`} value={filter.action} onChange={event => updateFilter({ action: event.target.value as EvidenceReviewFilter["action"] })}>
          <option value="all">All statuses</option><option value="error">Errors</option><option value="create">Create</option><option value="skip">Exact duplicates</option>
        </select></div>
      <div className="field"><label htmlFor={`${id}-type`}>Evidence type</label>
        <select id={`${id}-type`} value={filter.recordType} onChange={event => updateFilter({ recordType: event.target.value })}>
          <option value="all">All types</option><option value="market_price">Prices</option><option value="fx_rate">FX observations</option><option value="invalid">Invalid type</option>
        </select></div>
      <div className="field"><label htmlFor={`${id}-field`}>Problem field</label>
        <select id={`${id}-field`} value={filter.field} onChange={event => updateFilter({ field: event.target.value })}>
          <option value="all">All fields</option>{fields.map(field => <option key={field}>{field}</option>)}
        </select></div>
      <div className="field"><label htmlFor={`${id}-query`}>Find row or validation message</label>
        <input id={`${id}-query`} value={filter.query} onChange={event => updateFilter({ query: event.target.value })} maxLength={200} type="search" /></div>
    </div>
    <div className="button-row">
      <button className="button-secondary" type="button" disabled={!issues.length} onClick={() => navigateIssue(-1)}>Previous error</button>
      <button className="button-secondary" type="button" disabled={!issues.length} onClick={() => navigateIssue(1)}>Next error</button>
      <button className="button-secondary" type="button" onClick={() => { setFilter(EMPTY_EVIDENCE_FILTER); setPage(0); setSelectedRow(null); setMessage(""); }}>Reset filters</button>
      <label htmlFor={`${id}-jump`}>CSV row</label>
      <input className="evidence-row-jump" id={`${id}-jump`} type="number" min={2} step={1} value={jump} onChange={event => setJump(event.target.value)} />
      <button className="button-secondary" type="button" disabled={!jump} onClick={jumpToRow}>Go to row</button>
    </div>
    <p role="status">{filtered.length} of {rows.length} rows match. {message} Filtering does not change the file or apply counts.</p>
    <div className="table-wrap" role="region" aria-label="Evidence preview rows" tabIndex={0}>
      <table><caption className="sr-only">Server validation by original CSV row</caption>
        <thead><tr><th scope="col">CSV row</th><th scope="col">Type</th><th scope="col">Action</th><th scope="col">Result</th></tr></thead>
        <tbody>{visible.map(row => <tr key={row.row_index} tabIndex={-1} ref={selectedRow === row.row_index ? focusRow : undefined}
          className={selectedRow === row.row_index ? "evidence-row-selected" : undefined}>
          <th scope="row">{row.row_index}</th><td>{row.record_type || "Invalid"}</td>
          <td><span className={`badge ${row.action === "create" ? "badge-success" : row.action === "skip" ? "badge-warn" : "badge-danger"}`}>{row.action}</span></td>
          <td>{row.errors.length ? <ul>{row.errors.map((error, index) => <li key={`${error.field}-${index}`}><strong>{error.field}:</strong> {error.message}</li>)}</ul> : row.message}</td>
        </tr>)}</tbody>
      </table>
      {!visible.length && <p>No rows match these filters.</p>}
    </div>
    <div className="button-row" aria-label="Evidence preview pagination">
      <button className="button-secondary" type="button" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous page</button>
      <span>Page {currentPage + 1} of {pageCount} · up to {EVIDENCE_REVIEW_PAGE_SIZE} rows per page</span>
      <button className="button-secondary" type="button" disabled={currentPage + 1 >= pageCount} onClick={() => setPage(currentPage + 1)}>Next page</button>
    </div>
  </section>;
}
