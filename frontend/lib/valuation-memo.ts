import type { ValuationMemoResponse } from "./api/ai.ts";
import { sourceLink } from "./source-link.ts";

export type MemoSelection = {
  valuationId: number;
  assumptionSetId: number;
  scenario: string;
  assumptionsUpdatedAt: string;
  outputId?: number;
};

/** Include the saved update and calculation identity, not unsaved form values. */
export function memoSessionKey(selection: MemoSelection): string {
  return JSON.stringify(selection);
}

function sameTimestamp(left: string, right: string): boolean {
  if (left === right) return true;
  const parsed = Date.parse(left);
  return Number.isFinite(parsed) && parsed === Date.parse(right);
}

/** Legacy content stays visibly unverified; known mismatched evidence is withheld. */
export function memoBasisError(memo: ValuationMemoResponse, selected: MemoSelection): string | null {
  if (!memo.memo_markdown || !memo.evidence) return null;
  const basis = memo.evidence;
  if (basis.valuation_model_id !== selected.valuationId || basis.assumption_set_id !== selected.assumptionSetId
      || basis.scenario !== selected.scenario) {
    return "The returned memo belongs to a different saved model or scenario. Reload the selected memo.";
  }
  if (basis.assumptions_updated_at && !sameTimestamp(basis.assumptions_updated_at, selected.assumptionsUpdatedAt)) {
    return "The returned memo describes an earlier saved update. Generate a memo for the selected saved version.";
  }
  if (selected.outputId !== undefined && basis.output_id != null && basis.output_id !== selected.outputId) {
    return "The returned memo describes a different saved calculation. Reload the selected saved version.";
  }
  return null;
}

export function memoSourceAnchor(prefix: string, index: number): string {
  return `${prefix}-source-${index + 1}`;
}

/** Generated content may link to declared source anchors or safe external HTTP(S) URLs only. */
export function memoLink(href: string | undefined, sourceIds: readonly string[], prefix: string): string | null {
  if (!href) return null;
  for (let index = 0; index < sourceIds.length; index++) {
    const anchor = `#${memoSourceAnchor(prefix, index)}`;
    if (href === anchor || href === `source_id:${sourceIds[index]}`) return anchor;
  }
  return sourceLink(href);
}

/** Export identity comes exclusively from the displayed artifact, never current controls. */
export function valuationMemoExport(memo: ValuationMemoResponse) {
  const evidence = memo.evidence;
  const positiveId = (value: unknown) => typeof value === "number" && Number.isSafeInteger(value) && value > 0 ? value : "unverified";
  const outputId = positiveId(evidence?.ai_output_id ?? memo.ai_output_id);
  const filename = `valuation-${positiveId(evidence?.valuation_model_id)}-assumptions-${positiveId(evidence?.assumption_set_id)}-memo-${outputId}.md`;
  const isMock = Boolean(evidence?.is_mock || memo.is_mock);
  const content = `# Valuation memo\n\n**AI Interpretation${isMock ? " · Mock Data" : ""}**\n\nInterpretation quality is not evaluated. Source references do not establish financial correctness.\n\n## Saved evidence\n\n\`\`\`json\n${JSON.stringify(evidence ?? { status: "legacy_unverified", ai_output_id: memo.ai_output_id ?? null }, null, 2)}\n\`\`\`\n\n## Memo\n\n${memo.memo_markdown ?? ""}\n`;
  return { filename, content, mimeType: "text/markdown;charset=utf-8" };
}
