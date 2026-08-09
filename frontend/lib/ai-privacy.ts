export const AI_PRIVACY_DISCLOSURE_VERSION = "v1";

export const AI_DISCLOSURES = {
  documentSummary: "An external AI provider may receive the selected raw document text.",
  researchChat: "An external AI provider may receive all messages in this private research session.",
  narrativeToNumbers: "An external AI provider may receive your company narrative and current valuation assumptions.",
  valuationMemo: "An external AI provider may receive company metadata, valuation assumptions, and calculated DCF outputs.",
  narrativeExtraction: "An external AI provider may receive event titles and descriptions.",
  thesisImpact: "An external AI provider may receive the event text and your private active thesis assumptions. Results remain proposals until you apply them.",
} as const;
