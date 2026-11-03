import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";
import ts from "typescript";
import * as legacy from "./api.ts";
import { ApiError, errorResponse } from "./api/contract.ts";

const expectedExports = [
  "ApiError",
  "applyPeerCsv",
  "archivePeerValuationSet",
  "archiveValuationDraft",
  "calculateRealOption",
  "calculateSavedRealOption",
  "classifyEventImpact",
  "confirmIndustryMapping",
  "createDcfAssumptionSet",
  "createDecisionLog",
  "createEvidence",
  "createOrReopenValuationDraft",
  "createPeerValuationSet",
  "createValuationModel",
  "createVariantPerception",
  "default",
  "deleteApi",
  "deleteScoringConfig",
  "draftAutofillAssumptions",
  "exportData",
  "exportPeerValuationSet",
  "extractFinancialsFromFiling",
  "extractXbrl",
  "fetchAiCitationSuggestions",
  "fetchAllIndustryCandidates",
  "fetchApi",
  "fetchApiResponse",
  "fetchCurrentMarketRegime",
  "fetchDebtRatioPrior",
  "fetchDecisionLogs",
  "fetchDividendPayoutPrior",
  "fetchDividendYieldPrior",
  "fetchEvidenceLedger",
  "fetchFinancialTrends",
  "fetchIndustryMappingCandidates",
  "fetchIndustryMix",
  "fetchLatestMarketPrice",
  "fetchMacroSectorSensitivity",
  "fetchMarketQuote",
  "fetchOAuthStatus",
  "fetchRawDocumentSummaries",
  "fetchResearchSession",
  "fetchValuationContext",
  "fetchValuationMemo",
  "fetchVariantPerceptions",
  "fetchVolatilityBenchmark",
  "generateAiSummary",
  "generateValuationMemo",
  "getDcfScenarios",
  "getFinancialCandidate",
  "getFinancialReconciliation",
  "getFinancialStatementIdentities",
  "getNormalizedCoverage",
  "getPeerCsvTemplate",
  "getPeerValuationSet",
  "getRelativeValuationCountries",
  "getRelativeValuationIndustries",
  "getSavedRelativeInputs",
  "getValuationChangeLogs",
  "getValuationModel",
  "getValuationModelAssumptions",
  "listAiOutputs",
  "listExtractedFinancialCandidates",
  "listFilingSections",
  "listFinancialPeriods",
  "listNormalizedSnapshots",
  "listPeerValuationSetRevisions",
  "listPeerValuationSets",
  "listPortfolioCashBalances",
  "listPortfolioSnapshots",
  "listValuationModels",
  "lookupCompanyByTicker",
  "mapEventToDcf",
  "normalizeFinancialPeriod",
  "overrideFinancialCandidate",
  "parseFilingSections",
  "patchApi",
  "postApi",
  "postApiFormData",
  "postFormApi",
  "previewPeerCsv",
  "promoteFinancialCandidates",
  "putApi",
  "refreshValuationDraft",
  "resetValuationDraftFields",
  "resolveStaleValuation",
  "restorePeerValuationSet",
  "reviewFinancialCandidate",
  "reviewPeerValuationSet",
  "runBottomUpMacroSensitivity",
  "runMacroScenario",
  "runNarrativeToNumbers",
  "runOptionEligibilityTest",
  "runRelativeValuation",
  "runSavedRelativeValuation",
  "runTopDownMacroSensitivity",
  "saveIndustryMix",
  "sendResearchMessage",
  "solveReverseDcf",
  "submitMarketRegimeInput",
  "updatePeerValuationSet",
  "updateValuationDraft",
  "uploadScreenerExport"
];

test("API compatibility entry point preserves every runtime export and error identity", () => {
  assert.deepEqual(Object.keys(legacy).sort(), expectedExports);
  assert.equal(legacy.ApiError, ApiError);
});

test("API modules keep transport, domain dependencies and the compatibility facade separate", () => {
  const directory = new URL("./api/", import.meta.url);
  for (const file of readdirSync(directory).filter(name => name.endsWith(".ts"))) {
    const source = readFileSync(new URL(file, directory), "utf8");
    assert.ok(source.split("\n").length <= 600, `${file}: split by responsibility before exceeding 600 lines`);
    const ast = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true);
    for (const statement of ast.statements) {
      if (!ts.isImportDeclaration(statement)) continue;
      const target = (statement.moduleSpecifier as ts.StringLiteral).text;
      assert.ok(!["../api.ts", "@/lib/api"].includes(target), `${file}: must not import the facade`);
      if (!statement.importClause?.isTypeOnly) {
        const allowed = file === "transport.ts" ? ["./contract.ts"] : ["./contract.ts", "./transport.ts", "../ai-privacy.ts"];
        assert.ok(allowed.includes(target), `${file}: runtime dependency ${target} crosses domains`);
      }
    }
    if (file !== "transport.ts") assert.doesNotMatch(source, /\bfetch\s*\(|process\.env/, file);
  }
  const facade = ts.createSourceFile("api.ts", readFileSync(new URL("./api.ts", import.meta.url), "utf8"), ts.ScriptTarget.Latest, true);
  assert.ok(facade.statements.every(ts.isExportDeclaration), "The facade must contain only compatibility exports");
});

test("shared error metadata creates fresh unavailable envelopes without stale or mock claims", () => {
  const one = errorResponse("API_ERROR", "Unavailable");
  const two = errorResponse("API_ERROR", "Unavailable");
  one.meta.warnings.push("local edit");
  assert.deepEqual(two.meta.warnings, ["Unavailable"]);
  assert.equal(two.meta.is_stale, false);
  assert.equal(two.meta.source, "transport");
  assert.equal(two.data, null);
});
