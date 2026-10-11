import type { AiCitationSuggestionCandidate, AiOutput } from "@/lib/api";


export type CitationDraft = {
  quote: string;
  start_char?: number;
  end_char?: number;
};


export function initialCitationDrafts(output: AiOutput): Record<string, CitationDraft> {
  return Object.fromEntries(
    output.citations_json
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
