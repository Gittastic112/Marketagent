export const AI_PRIVACY_DISCLOSURE_VERSION = "v1";

export const AI_DISCLOSURES = {
  documentSummary: "An external AI provider may receive the selected document text, or its title when text is unavailable.",
  researchChat: "An external AI provider may receive all messages in this private research session and titles/excerpts of up to three retrieved documents.",
  narrativeToNumbers: "An external AI provider may receive your company narrative, current valuation assumptions, and saved-version identifiers, dates, currency and output hash.",
  valuationMemo: "An external AI provider may receive company metadata, saved valuation name/type/scenario/version, assumptions and story text, and calculated DCF outputs and diagnostics.",
  narrativeExtraction: "An external AI provider may receive event titles and descriptions.",
  eventMapping: "An external AI provider may receive this event title and description. No portfolio, thesis, or valuation inputs are included.",
  thesisImpact: "An external AI provider may receive the event text and your private active thesis assumptions. Results remain proposals until you apply them.",
} as const;
