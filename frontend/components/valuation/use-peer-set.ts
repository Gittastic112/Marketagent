"use client";

import { createRequestGate } from "@/lib/latest-request";

import { useEffect, useMemo, useRef, useState } from "react";
import { applyPeerCsv, archivePeerValuationSet, createPeerValuationSet, exportPeerValuationSet, getPeerCsvTemplate, getPeerValuationSet, listPeerValuationSetRevisions, PeerMultipleMethod, PeerCsvPreview, PeerValuationSet, PeerValuationSetRevision, previewPeerCsv, restorePeerValuationSet, reviewPeerValuationSet, updatePeerValuationSet } from "@/lib/api/relative-valuation";
import { DraftMember, DraftTarget, blankTarget, fromTarget, targetPayload, blankMember, fromMember, toPayload, downloadCsv } from "./peer-set-fields";

export type PeerSetManagerProps = {
  companyId: number;
  peerSets: PeerValuationSet[];
  onChanged: () => Promise<void>;
  defaultOpen?: boolean;
};

export function usePeerSetManager({
  companyId,
  peerSets,
  onChanged,
  defaultOpen = false,
}: PeerSetManagerProps) {
  const requests = useMemo(createRequestGate, []);
  useEffect(() => () => requests.invalidate(), [requests]);
  const managerRef = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    const revealPeer = () => {
      const match = /^#peer-set-(\d+)$/.exec(window.location.hash);
      if (!match || !peerSets.some(set => String(set.id) === match[1])) return;
      if (managerRef.current) managerRef.current.open = true;
      const element = document.getElementById(`peer-set-${match[1]}`);
      element?.scrollIntoView({ block: "center" });
      element?.focus({ preventScroll: true });
    };
    revealPeer();
    window.addEventListener("hashchange", revealPeer);
    return () => window.removeEventListener("hashchange", revealPeer);
  }, [peerSets]);

  const [name, setName] = useState("");

  const [notes, setNotes] = useState("");

  const [members, setMembers] = useState<DraftMember[]>([blankMember(), blankMember(), blankMember()]);

  const [targetEnabled, setTargetEnabled] = useState(false);

  const [target, setTarget] = useState<DraftTarget>(blankTarget());

  const [editing, setEditing] = useState<PeerValuationSet | null>(null);

  const [history, setHistory] = useState<Record<number, PeerValuationSetRevision[] | undefined>>({});

  const [warningAcknowledgements, setWarningAcknowledgements] = useState<Record<number, boolean>>({});

  const [csvText, setCsvText] = useState("");

  const [csvPreview, setCsvPreview] = useState<PeerCsvPreview | null>(null);

  const [csvLoading, setCsvLoading] = useState(false);

  const csvSelection = useRef(0);

  const [busy, setBusy] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [message, setMessage] = useState<string | null>(null);

  const resetForm = () => {
    setEditing(null);
    setName("");
    setNotes("");
    setMembers([blankMember(), blankMember(), blankMember()]);
    setTargetEnabled(false);
    setTarget(blankTarget());
  };

  const updateMember = (index: number, patch: Partial<DraftMember>) => {
    setMembers((current) => current.map((member, memberIndex) => (
      memberIndex === index ? { ...member, ...patch } : member
    )));
  };

  const updateMultiple = (index: number, method: PeerMultipleMethod, value: string) => {
    setMembers((current) => current.map((member, memberIndex) => (
      memberIndex === index
        ? { ...member, multiples: { ...member.multiples, [method]: value } }
        : member
    )));
  };

  const saveSet = async () => {
    const isCurrent = requests.begin();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const payload = {
        name,
        notes: notes || undefined,
        targetContext: targetEnabled ? targetPayload(target) : editing ? null : undefined,
        members: members.map(toPayload),
      };
      if (editing) {
        await updatePeerValuationSet(editing.id, {
          ...payload,
          expectedVersion: editing.version,
        });
        if (!isCurrent()) return;
        setMessage("Peer set updated. Review was reset and the prior version remains in history.");
      } else {
        await createPeerValuationSet({ companyId, ...payload });
        if (!isCurrent()) return;
        setMessage("Draft peer set saved. Review every source before approving it for calculations.");
      }
      resetForm();
      await onChanged();
      if (!isCurrent()) return;
    } catch (caught) {
      if (!isCurrent()) return;
      setError(caught instanceof Error ? caught.message : "Could not save the peer set");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };

  const startEdit = async (peerSetId: number) => {
    const isCurrent = requests.begin();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const detail = await getPeerValuationSet(peerSetId);
      if (!isCurrent()) return;
      setEditing(detail);
      setName(detail.name);
      setNotes(detail.notes || "");
      setMembers((detail.members || []).map(fromMember));
      setTargetEnabled(Boolean(detail.targetContext));
      setTarget(detail.targetContext ? fromTarget(detail.targetContext) : blankTarget());
    } catch (caught) {
      if (!isCurrent()) return;
      setError(caught instanceof Error ? caught.message : "Could not load the peer set");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };

  const reviewSet = async (peerSet: PeerValuationSet) => {
    const isCurrent = requests.begin();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await reviewPeerValuationSet(peerSet.id, peerSet.version, peerSet.diagnostics);
      if (!isCurrent()) return;
      setWarningAcknowledgements((current) => ({ ...current, [peerSet.id]: false }));
      setMessage("Peer evidence and its current diagnostic warnings were acknowledged. The median is now available for relative valuation.");
      await onChanged();
      if (!isCurrent()) return;
    } catch (caught) {
      if (!isCurrent()) return;
      setError(caught instanceof Error ? caught.message : "Could not review the peer set");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };

  const archiveSet = async (peerSet: PeerValuationSet) => {
    const isCurrent = requests.begin();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await archivePeerValuationSet(peerSet.id, peerSet.version);
      if (!isCurrent()) return;
      setMessage("Peer set archived. Existing evidence and revision history were retained.");
      if (editing?.id === peerSet.id) resetForm();
      await onChanged();
      if (!isCurrent()) return;
    } catch (caught) {
      if (!isCurrent()) return;
      setError(caught instanceof Error ? caught.message : "Could not archive the peer set");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };

  const restoreSet = async (peerSet: PeerValuationSet) => {
    const isCurrent = requests.begin();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await restorePeerValuationSet(peerSet.id, peerSet.version);
      if (!isCurrent()) return;
      setMessage("Peer set restored as Draft. Review it again before using it in a valuation.");
      await onChanged();
      if (!isCurrent()) return;
    } catch (caught) {
      if (!isCurrent()) return;
      setError(caught instanceof Error ? caught.message : "Could not restore the peer set");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };

  const toggleHistory = async (peerSetId: number) => {
    const isCurrent = requests.begin();
    if (history[peerSetId]) {
      setHistory((current) => ({ ...current, [peerSetId]: undefined }));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const revisions = await listPeerValuationSetRevisions(peerSetId);
      if (!isCurrent()) return;
      setHistory((current) => ({ ...current, [peerSetId]: revisions }));
    } catch (caught) {
      if (!isCurrent()) return;
      setError(caught instanceof Error ? caught.message : "Could not load revision history");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };

  const downloadTemplate = async () => {
    const isCurrent = requests.begin();
    setBusy(true);
    setError(null);
    try {
      const template = await getPeerCsvTemplate();
      if (!isCurrent()) return;
      downloadCsv(template.filename, template.csvText);
    } catch (caught) {
      if (!isCurrent()) return;
      setError(caught instanceof Error ? caught.message : "Could not download the peer CSV template");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };

  const previewCsv = async () => {
    const isCurrent = requests.begin();
    setCsvPreview(null);
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const preview = await previewPeerCsv(companyId, csvText);
      if (!isCurrent()) return;
      setCsvPreview(preview);
    } catch (caught) {
      if (!isCurrent()) return;
      setError(caught instanceof Error ? caught.message : "Could not preview the peer CSV");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };

  const applyCsv = async () => {
    if (!csvPreview?.isValid || csvLoading || busy) return;
    const isCurrent = requests.begin();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const applied = await applyPeerCsv(companyId, csvText, csvPreview.sha256);
      if (!isCurrent()) return;
      setCsvText("");
      setCsvPreview(null);
      setMessage(
        applied.importDisposition === "reused"
          ? `This exact CSV was already applied. Reused ${applied.name} v${applied.version}${applied.isActive ? "" : " (archived)"}; no duplicate was created.`
          : "CSV applied as a Draft peer set. Review is still required before valuation use.",
      );
      try {
        await onChanged();
        if (!isCurrent()) return;
      } catch (caught) {
        if (!isCurrent()) return;
        setError(
          `The CSV is saved, but the peer-set list could not refresh. Retrying the exact file is safe. ${caught instanceof Error ? caught.message : ""
            }`.trim(),
        );
      }
    } catch (caught) {
      if (!isCurrent()) return;
      setCsvPreview(null);
      setError(caught instanceof Error ? caught.message : "Could not apply the peer CSV");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };

  const exportSet = async (peerSetId: number) => {
    const isCurrent = requests.begin();
    setBusy(true);
    setError(null);
    try {
      const exported = await exportPeerValuationSet(peerSetId);
      if (!isCurrent()) return;
      downloadCsv(exported.filename, exported.csvText);
      setMessage(exported.warnings.join(" "));
    } catch (caught) {
      if (!isCurrent()) return;
      setError(caught instanceof Error ? caught.message : "Could not export the peer set");
    } finally {
      if (!isCurrent()) return;
      setBusy(false);
    }
  };
  return { companyId, peerSets, defaultOpen, managerRef, name, setName, notes, setNotes, members, setMembers, targetEnabled, setTargetEnabled, target, setTarget, editing, history, warningAcknowledgements, setWarningAcknowledgements, csvText, setCsvText, csvPreview, setCsvPreview, csvLoading, setCsvLoading, csvSelection, busy, error, setError, message, setMessage, resetForm, updateMember, updateMultiple, saveSet, startEdit, reviewSet, archiveSet, restoreSet, toggleHistory, downloadTemplate, previewCsv, applyCsv, exportSet };
}
