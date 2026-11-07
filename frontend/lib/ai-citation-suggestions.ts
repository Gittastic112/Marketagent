import type { AiCitationSuggestionCandidate, AiOutput } from "@/lib/api";


export type CitationDraft = {
  quote: string;
  start_char?: number;
  end_char?: number;
};

export function readableCitations(output: Pick<AiOutput, "citations_json">) {
  return output.citations_json.map(citation => ({
    source_id: typeof citation.source_id === "string" ? citation.source_id : "Source unavailable",
    quote: typeof citation.quote === "string" ? citation.quote : "",
    status: typeof citation.status === "string" ? citation.status : "not_evaluated",
    reason: typeof citation.reason === "string" ? citation.reason : null,
    start_char: typeof citation.start_char === "number" && Number.isInteger(citation.start_char) && citation.start_char >= 0 ? citation.start_char : undefined,
    end_char: typeof citation.end_char === "number" && Number.isInteger(citation.end_char) && citation.end_char > 0 ? citation.end_char : undefined,
    internal_href: typeof citation.internal_href === "string" && /^\/(?![\/\\])/.test(citation.internal_href) ? citation.internal_href : null,
  }));
}

export function readableEvaluation(output: Pick<AiOutput, "evaluation_json">) {
  const evaluation = output.evaluation_json;
  const raw = evaluation?.checks;
  const checks = raw && typeof raw === "object" && !Array.isArray(raw) ? Object.entries(raw) : [];
  const claimReview = evaluation?.claim_review as {requires_review_notes?: unknown; claims?: unknown} | undefined;
  const claims = Array.isArray(claimReview?.claims) ? claimReview.claims : [];
  const claimFlags = claims.flatMap((claim: unknown) => {
    if (!claim || typeof claim !== "object") return [];
    const item = claim as {source_id?: unknown; claim_text?: unknown; flags?: unknown};
    if (!Array.isArray(item.flags)) return [];
    return item.flags.filter((flag: unknown): flag is {message: string; code: string} => !!flag && typeof flag === "object"
      && typeof (flag as {message?: unknown}).message === "string" && typeof (flag as {code?: unknown}).code === "string")
      .map(flag => ({...flag, sourceId: typeof item.source_id === "string" ? item.source_id : "Unknown source",
        claimText: typeof item.claim_text === "string" ? item.claim_text : ""}));
  });
  return {
    claimFlags,
    requiresReviewNotes: claimReview?.requires_review_notes === true,
    passed: evaluation?.passed === true && checks.length > 0
      && checks.every(([name, value]) => typeof value === "boolean" && (name === "citations_required" || value === true)),
    failedChecks: checks.filter(([name, value]) => name !== "citations_required" && value !== true).map(([name]) => name),
  };
}


export function initialCitationDrafts(output: AiOutput): Record<string, CitationDraft> {
  return Object.fromEntries(
    readableCitations(output)
      .filter((citation) => citation.source_id && citation.quote)
      .map((citation) => [
        citation.source_id,
        {
          quote: citation.quote,
          start_char: citation.start_char,
          end_char: citation.end_char,
        },
      ]),
  );
}


export function applyCitationCandidate(
  current: Record<string, CitationDraft>,
  sourceId: string,
  candidate: AiCitationSuggestionCandidate,
): Record<string, CitationDraft> {
  return {
    ...current,
    [sourceId]: {
      quote: candidate.quote,
      start_char: candidate.start_char,
      end_char: candidate.end_char,
    },
  };
}


export function applyManualCitationEdit(
  current: Record<string, CitationDraft>,
  sourceId: string,
  quote: string,
): Record<string, CitationDraft> {
  return { ...current, [sourceId]: { quote } };
}


export function buildCitationValidationPayload(
  sourceIds: string[],
  drafts: Record<string, CitationDraft>,
) {
  if (sourceIds.length === 0 || sourceIds.some((sourceId) => !drafts[sourceId]?.quote.trim())) {
    return null;
  }
  return {
    citations: sourceIds.map((source_id) => {
      const draft = drafts[source_id];
      return {
        source_id,
        quote: draft.quote.trim(),
        ...(draft.start_char != null && draft.end_char != null
          ? { start_char: draft.start_char, end_char: draft.end_char }
          : {}),
      };
    }),
  };
}
